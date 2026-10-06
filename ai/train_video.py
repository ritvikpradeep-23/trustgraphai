"""Step 4: train the video detector's head (your layer on top of EfficientNet-B0).

    python train_video.py                          # stage 1 only: backbone frozen
    python train_video.py --unfreeze-last 2        # then stage 2: last 2 blocks adapt too

Reads data/detection/splits/video/train.csv and val.csv (made by prepare_data.py).
The test batches are never opened here.

Stage 1 (always): EfficientNet is FROZEN. Each face crop becomes 1280 features
once, and only the head learns. Fast, needs little data, can't damage what
EfficientNet already knows.
Stage 2 (optional): the last N blocks also learn, at a learning rate 100x
lower than the head's, so they adjust gently instead of being overwritten.

Face crops are cached in data/detection/cache/faces/ so videos are decoded once.
The result is saved to models/efficientnet_head.pt (video.model_path in
detection_config.json), with the validation scores stored inside the file.
"""
import argparse
import hashlib
import random
import sys
from datetime import date
from pathlib import Path

import cv2
import numpy as np
import torch

# The AI engine (EfficientNet-B0 + your layer) lives in backend/app/ai, shared with the server.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))  # the website backend holds the engine code

from app.ai import efficientnet_wrapper as effnet  # noqa: E402
from app.ai.combined_model import new_head, save_head  # noqa: E402
from app.ai.face_detector import FaceDetector  # noqa: E402
from detection_common import ROOT, best_device, load_config, metrics, read_csv, resolve, split_dir  # noqa: E402
from video_detector import FACE_MARGIN, face_crops, pixel_batch  # noqa: E402

CACHE = ROOT / "data" / "detection" / "cache" / "faces"


def cached_crops(path: str, n_frames: int, detector: FaceDetector) -> list[Path]:
    """Face crops for one video, saved as JPG files the first time."""
    folder = CACHE / f"{n_frames}f" / hashlib.sha1(path.encode("utf-8")).hexdigest()[:16]
    files = sorted(folder.glob("*.jpg"))
    if not files:
        folder.mkdir(parents=True, exist_ok=True)
        crops, _ = face_crops(path, n_frames, detector)
        for i, crop in enumerate(crops):
            cv2.imwrite(str(folder / f"{i:03d}.jpg"), crop)
        files = sorted(folder.glob("*.jpg"))
    return files


def load_frames(rows, n_frames):
    """[(crop file, label, video index)] for every frame of every video."""
    detector = FaceDetector(FACE_MARGIN)
    items = []
    for v, row in enumerate(rows):
        for f in cached_crops(row["path"], n_frames, detector):
            items.append((f, row["label"], v))
    return items


def features(items, model, device, batch_size=32) -> torch.Tensor:
    backbone = model.efficientnet.to(device).eval()
    out = []
    with torch.inference_mode():
        for i in range(0, len(items), batch_size):
            crops = [cv2.imread(str(f)) for f, _, _ in items[i:i + batch_size]]
            out.append(backbone(pixel_values=pixel_batch(crops, effnet.MODEL_ID).to(device)).pooler_output.cpu())
    return torch.cat(out)


def video_scores(frame_scores, items, n_videos) -> np.ndarray:
    """Average the frame scores of each video (the same rule the detector uses)."""
    sums, counts = np.zeros(n_videos), np.zeros(n_videos)
    for s, (_, _, v) in zip(frame_scores, items):
        sums[v] += s
        counts[v] += 1
    return sums / np.maximum(counts, 1)


def stage1(train_items, val_items, n_val, val_labels, model, device, epochs, lr, seed):
    torch.manual_seed(seed)
    print(f"Stage 1: frozen EfficientNet, features for {len(train_items) + len(val_items)} face crops...")
    x_tr = features(train_items, model, device)
    x_val = features(val_items, model, device)
    y_tr = torch.tensor([[float(y)] for _, y, _ in train_items])
    head = new_head().to(device)
    pos_weight = torch.tensor([(y_tr == 0).sum() / max((y_tr == 1).sum(), 1)], device=device)  # balance classes
    loss_fn = torch.nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    opt = torch.optim.Adam(head.parameters(), lr=lr, weight_decay=1e-4)
    for epoch in range(epochs):
        order = torch.randperm(len(x_tr))
        total = 0.0
        for i in range(0, len(order), 64):
            idx = order[i:i + 64]
            opt.zero_grad()
            loss = loss_fn(head(x_tr[idx].to(device)), y_tr[idx].to(device))
            loss.backward()
            opt.step()
            total += loss.item() * len(idx)
        print(f"  epoch {epoch + 1}/{epochs}  loss {total / len(x_tr):.4f}")
    with torch.no_grad():
        frame_s = torch.sigmoid(head(x_val.to(device))).squeeze(1).cpu().numpy()
    return head, metrics(val_labels, video_scores(frame_s, val_items, n_val))


def stage2(head, train_items, val_items, n_val, val_labels, model, device, epochs, lr, n_blocks, seed):
    """Fine-tune the last n_blocks of EfficientNet together with the head."""
    backbone = model.efficientnet.to(device)
    for p in backbone.parameters():
        p.requires_grad = False
    enc = backbone.encoder
    tuned = [p for m in [*enc.blocks[-n_blocks:], enc.top_conv, enc.top_bn] for p in m.parameters()]
    for p in tuned:
        p.requires_grad = True
    opt = torch.optim.Adam([{"params": head.parameters(), "lr": lr},
                            {"params": tuned, "lr": lr / 100}])  # much lower: nudge, don't overwrite
    loss_fn = torch.nn.BCEWithLogitsLoss()
    print(f"Stage 2: fine-tuning the last {n_blocks} blocks at lr {lr / 100:g} (head {lr:g})")
    items = list(train_items)
    for epoch in range(epochs):
        backbone.train()
        random.Random(seed + epoch).shuffle(items)
        total = 0.0
        for i in range(0, len(items), 16):
            batch = items[i:i + 16]
            pix = pixel_batch([cv2.imread(str(f)) for f, _, _ in batch], effnet.MODEL_ID).to(device)
            y = torch.tensor([[float(lbl)] for _, lbl, _ in batch], device=device)
            opt.zero_grad()
            loss = loss_fn(head(backbone(pixel_values=pix).pooler_output), y)
            loss.backward()
            opt.step()
            total += loss.item() * len(batch)
        print(f"  epoch {epoch + 1}/{epochs}  loss {total / len(items):.4f}")
    backbone.eval()
    with torch.no_grad():
        frame_s = torch.sigmoid(head(features(val_items, model, device).to(device))).squeeze(1).cpu().numpy()
    for p in backbone.parameters():
        p.requires_grad = False
    return metrics(val_labels, video_scores(frame_s, val_items, n_val)), backbone


def main(argv=None):
    cfg = load_config()["video"]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--epochs", type=int, default=30, help="stage 1 passes over the training frames")
    ap.add_argument("--lr", type=float, default=1e-3, help="head learning rate (stage 2 backbone gets lr/100)")
    ap.add_argument("--unfreeze-last", type=int, default=0, help="stage 2: fine-tune the last N blocks (0 = skip)")
    ap.add_argument("--finetune-epochs", type=int, default=2, help="stage 2 passes over the training frames")
    ap.add_argument("--frames", type=int, default=cfg["frames_per_video"], help="frames sampled per video")
    ap.add_argument("--max-videos", type=int, help="use only this many training videos (quick test)")
    ap.add_argument("--out", default=cfg["model_path"])
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)

    train = read_csv(split_dir("video") / "train.csv")
    val = read_csv(split_dir("video") / "val.csv")
    if args.max_videos:
        train = random.Random(args.seed).sample(train, min(args.max_videos, len(train)))
    device = best_device()
    print(f"{len(train)} training videos, {len(val)} validation videos, device: {device}")
    train_items, val_items = load_frames(train, args.frames), load_frames(val, args.frames)
    val_labels = [r["label"] for r in val]
    _, model = effnet.load(effnet.MODEL_ID)

    head, val_metrics = stage1(train_items, val_items, len(val), val_labels, model, device,
                               args.epochs, args.lr, args.seed)
    print(f"Validation after stage 1 (videos): {fmt(val_metrics)}")
    extra = {}
    if args.unfreeze_last:
        val_metrics, backbone = stage2(head, train_items, val_items, len(val), val_labels, model, device,
                                       args.finetune_epochs, args.lr, args.unfreeze_last, args.seed)
        print(f"Validation after stage 2 (videos): {fmt(val_metrics)}")
        # The head only matches the backbone it was trained with, so that is saved too (~16 MB).
        extra["backbone_state_dict"] = {k: v.cpu() for k, v in backbone.state_dict().items()}
    out = resolve(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    save_head(head.cpu(), str(out), model_id=effnet.MODEL_ID, trained=date.today().isoformat(),
              n_train_videos=len(train), n_val_videos=len(val), frames=args.frames, val_metrics=val_metrics,
              unfreeze_last=args.unfreeze_last, **extra)
    print(f"Saved {out}")
    return val_metrics


def fmt(m: dict) -> str:
    auc = "n/a" if m["roc_auc"] is None else f"{m['roc_auc']:.3f}"
    return f"accuracy {m['accuracy']:.1%}, F1 {m['f1']:.2f}, ROC-AUC {auc} (n={m['n']})"


if __name__ == "__main__":
    main()

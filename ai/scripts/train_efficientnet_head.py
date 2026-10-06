"""Train the small real/fake layer ("head") that sits on top of EfficientNet-B0.

    python scripts/train_efficientnet_head.py --data path/to/faces
    python scripts/train_efficientnet_head.py --data path/to/faces --unfreeze-last 2   # fine-tune, slower

The data folder needs two sub-folders of images (face crops work best):

    faces/
      real/   video001/frame_01.jpg ...   or just real/img001.jpg ...
      fake/   video101/frame_01.jpg ...

Frames from one video are nearly identical, so if you put each video's frames
in its own sub-folder, the train/validation split keeps whole videos on one
side. Otherwise validation would be scored on near-copies of training images
and look far better than it really is.

Default (frozen backbone): EfficientNet turns every image into 1280 features
ONCE, then only the head trains on those features. Fast on a laptop CPU.
--unfreeze-last N also lets the last N blocks adapt, with a 100x lower
learning rate than the head so the pretrained knowledge isn't wiped out.
The first run downloads google/efficientnet-b0 (~21 MB; public, no token).
"""
import argparse
import random
import sys
from datetime import date
from pathlib import Path

import numpy as np
import torch

sys.path[:0] = [str(Path(__file__).resolve().parents[2] / "backend"), str(Path(__file__).resolve().parents[1])]  # website backend, ai/
from app.ai import efficientnet_wrapper as effnet  # noqa: E402
from app.ai.combined_model import new_head, save_head  # noqa: E402

IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def find_images(data: Path) -> list[tuple[Path, int, str]]:
    """(image path, label 1 = fake / 0 = real, group) for every image."""
    items = []
    for label_name, label in (("real", 0), ("fake", 1)):
        folder = data / label_name
        if not folder.is_dir():
            raise SystemExit(f"missing folder: {folder}")
        for p in sorted(folder.rglob("*")):
            if p.suffix.lower() in IMAGE_TYPES:
                rel = p.relative_to(folder)
                group = f"{label_name}/{rel.parts[0]}" if len(rel.parts) > 1 else f"{label_name}/{p.name}"
                items.append((p, label, group))
    return items


def split_by_group(items, val_share: float, seed: int):
    groups = sorted({g for _, _, g in items})
    random.Random(seed).shuffle(groups)
    val_groups = set(groups[:max(1, int(len(groups) * val_share))])
    train = [i for i in items if i[2] not in val_groups]
    val = [i for i in items if i[2] in val_groups]
    return train, val


def evaluate(scores: np.ndarray, labels: np.ndarray) -> dict:
    from sklearn.metrics import roc_auc_score
    out = {"accuracy": float(((scores >= 0.5) == labels).mean())}
    if len(set(labels.tolist())) == 2:
        out["roc_auc"] = float(roc_auc_score(labels, scores))
    return out


def train_frozen(train, val, epochs: int, lr: float, model_id: str, seed: int):
    torch.manual_seed(seed)
    print(f"Extracting EfficientNet features for {len(train) + len(val)} images (done once)...")
    feats = {p: torch.from_numpy(effnet.extract_features(str(p), model_id)) for p, _, _ in train + val}
    x_tr = torch.stack([feats[p] for p, _, _ in train])
    y_tr = torch.tensor([[float(y)] for _, y, _ in train])
    head = new_head()
    # Weight the rarer class up so the head doesn't just learn "always say the common label".
    pos_weight = torch.tensor([(y_tr == 0).sum() / max((y_tr == 1).sum(), 1)])
    loss_fn = torch.nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    opt = torch.optim.Adam(head.parameters(), lr=lr, weight_decay=1e-4)
    for epoch in range(epochs):
        opt.zero_grad()
        loss = loss_fn(head(x_tr), y_tr)
        loss.backward()
        opt.step()
        if epoch % max(1, epochs // 5) == 0 or epoch == epochs - 1:
            print(f"  epoch {epoch + 1}/{epochs}  loss {loss.item():.4f}")
    with torch.no_grad():
        val_scores = torch.sigmoid(head(torch.stack([feats[p] for p, _, _ in val]))).squeeze(1).numpy()
    return head, val_scores


def train_unfrozen(train, val, epochs: int, lr: float, n_blocks: int, model_id: str, seed: int):
    """Fine-tuning: the last n blocks and the head train together on the images."""
    torch.manual_seed(seed)
    _, full = effnet.load(model_id)
    backbone = full.efficientnet
    for p in backbone.parameters():
        p.requires_grad = False
    encoder = backbone.encoder
    tuned = [p for m in [*encoder.blocks[-n_blocks:], encoder.top_conv, encoder.top_bn] for p in m.parameters()]
    for p in tuned:
        p.requires_grad = True
    head = new_head()
    opt = torch.optim.Adam([{"params": head.parameters(), "lr": lr},
                            {"params": tuned, "lr": lr / 100}])  # much lower: nudge, don't overwrite
    loss_fn = torch.nn.BCEWithLogitsLoss()
    for epoch in range(epochs):
        backbone.train()
        random.Random(seed + epoch).shuffle(train)
        total = 0.0
        for start in range(0, len(train), 16):
            batch = train[start:start + 16]
            pix = torch.cat([effnet.pixel_inputs(str(p), model_id)["pixel_values"] for p, _, _ in batch])
            y = torch.tensor([[float(lbl)] for _, lbl, _ in batch])
            opt.zero_grad()
            loss = loss_fn(head(backbone(pixel_values=pix).pooler_output), y)
            loss.backward()
            opt.step()
            total += loss.item() * len(batch)
        print(f"  epoch {epoch + 1}/{epochs}  loss {total / len(train):.4f}")
    backbone.eval()
    with torch.no_grad():
        val_scores = np.array([float(torch.sigmoid(head(backbone(**effnet.pixel_inputs(str(p), model_id)).pooler_output)))
                               for p, _, _ in val])
    return head, val_scores, backbone


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True, help="folder with real/ and fake/ sub-folders")
    ap.add_argument("--out", default="models/efficientnet_head.pt")
    ap.add_argument("--epochs", type=int, default=300, help="frozen: full-batch steps; unfrozen: passes over the data")
    ap.add_argument("--lr", type=float, default=1e-3, help="head learning rate (backbone gets lr/100)")
    ap.add_argument("--val-share", type=float, default=0.2)
    ap.add_argument("--unfreeze-last", type=int, default=0, help="fine-tune the last N blocks (0 = frozen)")
    ap.add_argument("--model-id", default=effnet.MODEL_ID)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)

    items = find_images(Path(args.data))
    train, val = split_by_group(items, args.val_share, args.seed)
    print(f"{len(items)} images: {len(train)} train, {len(val)} validation "
          f"({sum(y for _, y, _ in items)} fake, {sum(1 - y for _, y, _ in items)} real)")
    if args.unfreeze_last:
        head, val_scores, backbone = train_unfrozen(train, val, args.epochs, args.lr, args.unfreeze_last,
                                                    args.model_id, args.seed)
        # The head only works with the backbone it was trained with, so the
        # fine-tuned backbone is saved alongside it (~16 MB instead of ~6 KB).
        extra = {"backbone_state_dict": backbone.state_dict()}
    else:
        head, val_scores = train_frozen(train, val, args.epochs, args.lr, args.model_id, args.seed)
        extra = {}
    labels = np.array([y for _, y, _ in val])
    metrics = evaluate(val_scores, labels)
    print(f"Validation ({len(val)} images, whole groups held out): {metrics}")
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    save_head(head, args.out, model_id=args.model_id, trained=date.today().isoformat(), n_train=len(train),
              n_val=len(val), val_metrics=metrics, unfreeze_last=args.unfreeze_last, data=str(args.data), **extra)
    print(f"Saved {args.out}. Use it with DEEPFAKE_MODE=efficientnet (or both).")
    return metrics


if __name__ == "__main__":
    main()

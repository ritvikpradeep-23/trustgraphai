"""Step 5: fine-tune the AI-text detector on the human-vs-AI training split.

    python train_text.py                         # distilroberta-base, 2 epochs
    python train_text.py --epochs 1 --max-train 400      # quick test

Reads data/detection/splits/text/train.csv and val.csv (made by prepare_data.py).
The test batches are never opened here. The first run downloads the base
model from Hugging Face (distilroberta-base is about 330 MB; public, no token).
The best epoch on VALIDATION is kept and saved to models/text_detector.
"""
import argparse
import json
import random
from datetime import date

import torch

from detection_common import best_device, load_config, metrics, read_csv, resolve, split_dir


def batches(rows, size, seed=None):
    rows = list(rows)
    if seed is not None:
        random.Random(seed).shuffle(rows)
    for i in range(0, len(rows), size):
        yield rows[i:i + size]


def evaluate(model, tokenizer, rows, device, max_length, batch_size=64) -> dict:
    model.eval()
    scores = []
    with torch.inference_mode():
        for batch in batches(rows, batch_size):
            enc = tokenizer([r["text"] for r in batch], truncation=True, max_length=max_length, padding=True,
                            return_tensors="pt").to(device)
            scores += model(**enc).logits.softmax(-1)[:, 1].float().cpu().tolist()
    return metrics([r["label"] for r in rows], scores)


def main(argv=None):
    cfg = load_config()["text"]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-model", default=cfg["base_model"], help="Hugging Face model name or a local folder")
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--batch-size", type=int, default=16)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--max-length", type=int, default=cfg["max_length"])
    ap.add_argument("--max-train", type=int, help="use only this many training texts (quick test)")
    ap.add_argument("--max-val", type=int, help="use only this many validation texts (quick test)")
    ap.add_argument("--out", default=cfg["model_dir"])
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup

    torch.manual_seed(args.seed)
    train = read_csv(split_dir("text") / "train.csv")
    val = read_csv(split_dir("text") / "val.csv")
    if args.max_train:
        train = random.Random(args.seed).sample(train, min(args.max_train, len(train)))
    if args.max_val:
        val = random.Random(args.seed).sample(val, min(args.max_val, len(val)))
    device = best_device()
    print(f"{len(train)} training texts, {len(val)} validation texts, base model {args.base_model}, device {device}")

    tokenizer = AutoTokenizer.from_pretrained(args.base_model)
    model = AutoModelForSequenceClassification.from_pretrained(
        args.base_model, num_labels=2, id2label={0: "human", 1: "AI"}, label2id={"human": 0, "AI": 1}).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    steps = args.epochs * ((len(train) + args.batch_size - 1) // args.batch_size)
    sched = get_linear_schedule_with_warmup(opt, num_warmup_steps=int(0.06 * steps), num_training_steps=steps)
    # bfloat16 on GPUs that support it (RTX 30xx and newer): faster, less memory, no loss scaling needed.
    use_amp = device == "cuda" and torch.cuda.is_bf16_supported()

    out = resolve(args.out)
    best = None
    for epoch in range(args.epochs):
        model.train()
        total, seen = 0.0, 0
        for step, batch in enumerate(batches(train, args.batch_size, seed=args.seed + epoch)):
            enc = tokenizer([r["text"] for r in batch], truncation=True, max_length=args.max_length, padding=True,
                            return_tensors="pt").to(device)
            labels = torch.tensor([r["label"] for r in batch], device=device)
            with torch.autocast(device_type=device, dtype=torch.bfloat16, enabled=use_amp):
                loss = model(**enc, labels=labels).loss
            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            total, seen = total + loss.item() * len(batch), seen + len(batch)
            if step % 100 == 0:
                print(f"  epoch {epoch + 1} step {step}  loss {total / seen:.4f}")
        val_m = evaluate(model, tokenizer, val, device, args.max_length)
        print(f"Epoch {epoch + 1}/{args.epochs}: validation accuracy {val_m['accuracy']:.1%}, F1 {val_m['f1']:.2f}")
        if best is None or val_m["f1"] > best["f1"]:  # keep the best epoch on validation (never on test)
            best = val_m
            out.mkdir(parents=True, exist_ok=True)
            model.save_pretrained(out)
            tokenizer.save_pretrained(out)
            (out / "training_info.json").write_text(json.dumps({
                "base_model": args.base_model, "trained": date.today().isoformat(), "epoch": epoch + 1,
                "n_train": len(train), "n_val": len(val), "max_length": args.max_length, "val_metrics": val_m},
                indent=2), encoding="utf-8")
    print(f"Saved {out} (best validation F1 {best['f1']:.2f})")
    return best


if __name__ == "__main__":
    main()

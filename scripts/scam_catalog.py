"""Public demo catalog loader and explicit provenance labels."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SCAMSHIELD_DATASET = "sidzzz07/scamshield-dataset"

def load_catalog():
    return [*json.loads((ROOT / "data/demo_scam_patterns.json").read_text(encoding="utf-8")),
            *json.loads((ROOT / "data/scamshield_patterns.json").read_text(encoding="utf-8"))]

def seed_metadata(item):
    if item.get("source_dataset") == SCAMSHIELD_DATASET:
        return "scamshield_dataset", "synthetic_dataset", "ScamShield: " + item["title"]
    return "demo_pattern", "synthetic_demo", "Demo: " + item["title"]

def skeleton(text):
    return re.sub(r"\d+", "number", " ".join(re.findall(r"\w+", text.casefold())))

def validate_catalog(patterns):
    ids = [p["id"] for p in patterns]
    texts = [skeleton(p["text"]) for p in patterns]
    if len(ids) != len(set(ids)) or len(texts) != len(set(texts)):
        raise ValueError("Duplicate ID, normalized text, or number-only variant in catalog")
    if any(len(p["id"]) > 57 or len(seed_metadata(p)[2]) > 64 or len(texts[i]) < 24 for i, p in enumerate(patterns)):
        raise ValueError("Catalog violates database field limits or minimum text length")
    return len(patterns)

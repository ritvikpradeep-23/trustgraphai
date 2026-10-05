"""Where model files are loaded from.

Set TRUSTGRAPH_MODEL_DIR to a folder (for example a candidate bundle,
models/candidate/fast_r05) to run the engine on its files. Any file missing
from that folder falls back to models/, so a bundle only needs the files it
changes. Without the variable, everything loads from models/ as before.
"""
import os

DEFAULT_DIR = "models"


def model_path(name: str) -> str:
    custom = os.environ.get("TRUSTGRAPH_MODEL_DIR")
    if custom and os.path.exists(os.path.join(custom, name)):
        return os.path.join(custom, name)
    return os.path.join(DEFAULT_DIR, name)

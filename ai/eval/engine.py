"""Score evaluation messages with the TrustGraph engine, read-only.

Settings for what the engine is given alongside the text:
  text_only        just the message (what a text-only client sends). Urgent
                   words are counted from the text, the same way the website does.
  metadata_same    plus hour_of_day, contact_freq_24h, new_channel_flag drawn from
                   ONE distribution for scam and legit alike: no built-in signal.
  metadata_skewed  ASSUMPTION: scams get later hours, more contacts and more new
                   channels. Shows what metadata could add if it behaves this way.

Component scores are computed once and cached; only similarity is recomputed
when the reference corpus changes (leave-one-category-out, report-once).
"""
import hashlib
from contextlib import contextmanager

import numpy as np

from trustgraph.anomaly.detector import anomaly_score
from trustgraph.continuity.detector import continuity_score
from trustgraph.fusion import fuse
from trustgraph.precedent.detector import precedent_score
from trustgraph.signal import RiskSignal
from trustgraph.similarity import detector as sim
from trustgraph.similarity.corpus import LEGIT_MESSAGES, SCAM_SCRIPTS
from trustgraph.web.server import _URGENCY

SETTINGS = ["text_only", "metadata_same", "metadata_skewed"]
_HOUR_P = np.array([0.5, 0.3, 0.2, 0.2, 0.3, 0.5, 1.0, 2.0, 4.0, 6.0, 7.0, 7.0,
                    6.0, 7.0, 7.0, 6.0, 6.0, 5.0, 3.0, 1.5, 1.0, 0.8, 0.6, 0.5])
_HOUR_P = _HOUR_P / _HOUR_P.sum()
_LATE_P = np.roll(_HOUR_P, 9)  # same shape shifted toward evening and night
_LATE_P = _LATE_P / _LATE_P.sum()


def _rng_for(msg_id: str, setting: str):
    """Deterministic per message, so every run gives the same metadata."""
    digest = hashlib.sha256(f"{msg_id}:{setting}".encode()).digest()
    return np.random.default_rng(int.from_bytes(digest[:8], "little"))


def interaction_for(row: dict, setting: str) -> dict:
    text = row["text"]
    inter = {"message_text": text, "urgency_score": len(_URGENCY.findall(text))}
    if setting == "text_only":
        return inter
    rng = _rng_for(row["id"], setting)
    skew = setting == "metadata_skewed" and row["label"] == "scam"
    inter["hour_of_day"] = int(rng.choice(24, p=_LATE_P if skew else _HOUR_P))
    inter["contact_freq_24h"] = int(rng.poisson(2.5 if skew else 0.8))
    inter["new_channel_flag"] = int(rng.random() < (0.6 if skew else 0.05))
    return inter


def similarity_parts(text: str) -> dict:
    text = " ".join(text.split())[:sim.MAX_CHARS]
    match, category, closeness, flags, combined = sim.components(text)
    flag_score = 1.0 - float(np.prod([1.0 - e for e, _ in flags])) if flags else 0.0
    return {"wording": match, "flags": flag_score, "similarity": combined,
            "flag_reasons": [r for _, r in flags], "closest": category}


def score_rows(rows: list[dict], setting: str) -> list[dict]:
    """Every signal's score plus the fused score, for each message."""
    out = []
    for row in rows:
        inter = interaction_for(row, setting)
        parts = similarity_parts(row["text"])
        signals = [continuity_score(inter), RiskSignal("similarity", parts["similarity"], ""),
                   precedent_score(inter), anomaly_score(inter)]
        by = {s.signal_name: s for s in signals}
        out.append({"id": row["id"], "wording": parts["wording"], "flags": parts["flags"],
                    "similarity": parts["similarity"], "anomaly": by["anomaly"].score,
                    "continuity": by["continuity"].score, "precedent": by["precedent"].score,
                    "fused": fuse(signals).score, "anomaly_why": by["anomaly"].explanation,
                    "flag_reasons": parts["flag_reasons"], "closest": parts["closest"]})
    return out


def refuse(scores: list[dict], rows: list[dict]) -> list[dict]:
    """Recompute similarity (current corpus) and the fused score, keeping cached signals."""
    out = []
    for sc, row in zip(scores, rows):
        parts = similarity_parts(row["text"])
        signals = [RiskSignal("continuity", sc["continuity"], ""), RiskSignal("similarity", parts["similarity"], ""),
                   RiskSignal("precedent", sc["precedent"], ""), RiskSignal("anomaly", sc["anomaly"], "")]
        out.append({**sc, "wording": parts["wording"], "flags": parts["flags"], "similarity": parts["similarity"],
                    "fused": fuse(signals).score, "flag_reasons": parts["flag_reasons"], "closest": parts["closest"]})
    return out


@contextmanager
def corpus(scam_scripts: dict[str, list[str]] | None = None, legit_messages: list[str] | None = None):
    """Temporarily swap the similarity signal's reference corpus (experiment only)."""
    saved = sim._index
    sim._index = sim.build_index(scam_scripts if scam_scripts is not None else SCAM_SCRIPTS,
                                 legit_messages if legit_messages is not None else LEGIT_MESSAGES)
    try:
        yield
    finally:
        sim._index = saved


def explain(row: dict, setting: str) -> str:
    """The engine's own fused explanation for one message."""
    from trustgraph.pipeline import score_interaction
    return score_interaction(interaction_for(row, setting))[1].explanation

"""Similarity signal: does the message read like a known scam?

Two independent pieces of evidence, combined by noisy-OR:

1. Script match. TF-IDF (words + character n-grams, so paraphrases and typos
   still match) against reference scam scripts AND ordinary legit messages.
   What counts is how much closer the message is to the nearest scam than to
   the nearest legit message, so business or family vocabulary alone isn't
   enough.
2. Red flags. Specific asks that are scam tells regardless of wording
   (codes, gift-card numbers, remote access, a "safe account"). Urgency words
   are deliberately NOT a red flag here: the anomaly signal already counts them.

Interaction field: message_text (call transcript, SMS or email body).
"""
import math
import re

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion

from trustgraph.signal import RiskSignal
from trustgraph.similarity.corpus import LEGIT_MESSAGES, SCAM_SCRIPTS

MAX_CHARS = 5000

# Script-match score = logistic of (closest-scam similarity - closest-legit
# similarity): a margin of 0.10 gives 0.5, 0.20 about 0.88, 0 about 0.12.
MARGIN_MID = 0.10
MARGIN_SCALE = 0.05
MIN_SCAM_SIMILARITY = 0.15  # below this the message resembles no script at all
# Wording alone isn't proof: resembling a script can't push the signal past
# this on its own. A concrete scam ask (red flag) or another signal must agree.
MATCH_CAP = 0.6

# (evidence, plain-English reason, pattern). Evidence is a judgment call: how
# rarely an honest message makes this ask.
RED_FLAGS = [
    (0.8, "asks to move money to a 'safe' account",
     r"\b(safe|secure|protected|holding) account\b|\bmove (your|the) (money|funds|savings)\b"),
    (0.7, "asks for a one-time code, PIN or password",
     r"\b(read|send|tell|give|forward|share|confirm|reply with)\b.{0,40}"
     r"\b(otp|passcode|pin|password|(verification|security|one[- ]time|login|access|whatsapp|\d[- ]digit|six[- ]digit|sms) code)s?\b"
     r"|\b(read|send|tell|give|forward|share|confirm)\b.{0,40}\bcode\b.{0,40}\b(sent|texted|arrived|received)\b"),
    (0.7, "asks for gift-card codes",
     r"\b(buy|get|grab|purchase|pick up)\b.{0,40}\b(gift|steam|itunes|google play|apple|amazon) ?cards?\b"
     r"|\b(gift|steam|itunes|google play|apple|amazon) ?cards?\b.{0,80}\b(codes?|card numbers)\b"
     r"|\b(scratch|redemption)\b.{0,20}\bcodes?\b"),
    (0.7, "asks for remote access to a device",
     r"\b(anydesk|teamviewer|remote access|connect remotely|screen ?shar\w*|remote desktop)\b"),
    (0.5, "says the bank details have changed",
     r"\b(bank|banking|payment|account) details (have |has )?(changed|been updated)|\b(new|updated) (bank )?account\b.{0,40}\b(pay|payment|remit)"
     r"|\b(pay|remit)\b.{0,40}\b(new|updated) (bank )?account\b"),
    (0.5, "asks for payment in crypto",
     r"\b(bitcoin|btc|usdt|crypto(currency)?|wallet address)\b"),
    # Weak alone (surprise parties); scams pair secrecy with a money or code ask.
    (0.4, "asks to keep it secret",
     r"\b(don'?t|do not) (tell|mention it to|speak to|contact|call) (anyone|anybody|the (branch|bank|police)|police|mum|mom|dad|your (family|bank|wife|husband))"
     r"|\bkeep (this|it) (between us|confidential|quiet|secret)\b"),
    (0.5, "threatens arrest or legal action",
     r"\b(warrant|arrest(ed)?|deport(ed)?|lawsuit|court proceedings|legal action)\b"),
    (0.6, "threatens to share private videos or photos",
     r"\b(recorded|filmed|hacked) (you|your (webcam|camera|device|phone|computer))\b"
     r"|\b(compromising|intimate|explicit|private) (video|videos|photos?|pictures?|recording|footage)\b"
     # A threat to expose the reader to others: "pay or I'll send the video to all your
     # contacts", not "can you send the photos" or "I'll send you the photos".
     r"|\b(or|unless|otherwise|if you don'?t|i will|i'?ll|i am going to|i'?m going to)\b.{0,30}"
     r"\b(send|share|leak|post|publish|release|forward)\b.{0,40}\b(video|photos?|pictures?|recording|footage)\b"
     r".{0,40}\b(your (contacts|friends|family|colleagues|boss|employer|followers|address book)|"
     r"all your|everyone you know)\b"),
    # Honest employers don't charge you to start work: a job plus a payment ask is a strong tell.
    (0.7, "asks you to pay to get or start a job",
     r"\b(hired|job|role|position|vacancy|employment|start date|first (day|week|salary)|work(ing)? from home|remote work)\b"
     r".{0,120}\b(pay|send|transfer)\b.{0,40}\b(fee|charge|deposit|upfront|up front|in advance|kit|equipment|materials)\b"
     r"|\b(pay|send|transfer)\b.{0,40}\b(fee|charge|deposit|upfront|up front|in advance)\b"
     r".{0,120}\b(hired|job|role|position|start date|first (day|week|salary)|salary)\b"
     r"|\b(fee|charge|deposit)\b.{0,60}\bbefore (you|your) (start|first (day|shift)|begin)\b"
     r"|\bbefore (you|your) (start|first (day|shift)|begin)\b.{0,60}\b(fee|charge|deposit)\b"),
    (0.4, "asks for an upfront fee (to release money, a prize or a job)",
     # Everyday fees (training, registration, joining) are left out: clubs and schools charge them.
     r"\b(processing|release|clearance|administration|admin|withdrawal|handling|redelivery|background[- ]check|"
     r"activation|onboarding|unlock(ing)?) (fee|tax|charge|deposit)s?\b"
     r"|\bpay\b.{0,40}\b(upfront|up front|in advance|before (you|your) (start|first day))\b"),
]
_FLAGS = [(e, reason, re.compile(p, re.IGNORECASE | re.DOTALL)) for e, reason, p in RED_FLAGS]

# "Never share this code", "we will never ask you to move money": honest
# messages warn about exactly the asks scammers make.
_NEGATION = re.compile(
    r"\b(never|will not|won'?t|do not|don'?t)\s+(ask|share|give|send|tell|move|transfer|request|disclose|charge)\b[^.!?]{0,40}$",
    re.IGNORECASE)


def _flag_hits(text: str) -> list[tuple[float, str]]:
    hits = []
    for evidence, reason, pattern in _FLAGS:
        if any(not _NEGATION.search(text[:m.start()]) for m in pattern.finditer(text)):
            hits.append((evidence, reason))
    return hits


_index = None


def _build_index():
    global _index
    if _index is None:
        scam_texts, scam_labels = [], []
        for category, texts in SCAM_SCRIPTS.items():
            scam_texts += texts
            scam_labels += [category] * len(texts)
        vectorizer = FeatureUnion([
            ("words", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)),
            ("chars", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)),
        ])
        vectorizer.fit(scam_texts + LEGIT_MESSAGES)
        _index = {
            "vectorizer": vectorizer,
            "scam": vectorizer.transform(scam_texts),
            "scam_labels": scam_labels,
            "legit": vectorizer.transform(LEGIT_MESSAGES),
        }
    return _index


def _cosine_max(query, matrix) -> tuple[float, int]:
    # FeatureUnion concatenates two L2-normalized blocks, so each row has norm sqrt(2).
    sims = (matrix @ query.T).toarray().ravel() / 2.0
    best = int(np.argmax(sims))
    return float(sims[best]), best


def _script_match(text: str) -> tuple[float, str | None, float]:
    index = _build_index()
    query = index["vectorizer"].transform([text])
    scam_sim, best = _cosine_max(query, index["scam"])
    legit_sim, _ = _cosine_max(query, index["legit"])
    if scam_sim < MIN_SCAM_SIMILARITY:
        return 0.0, None, scam_sim
    score = 1.0 / (1.0 + math.exp(-((scam_sim - legit_sim) - MARGIN_MID) / MARGIN_SCALE))
    return min(score, MATCH_CAP), index["scam_labels"][best], scam_sim


def similarity_score(interaction: dict) -> RiskSignal:
    text = interaction.get("message_text")
    if not isinstance(text, str) or not text.strip():
        return RiskSignal(signal_name="similarity", score=0.0, explanation="No message text to compare")
    text = " ".join(text.split())[:MAX_CHARS]

    match_score, category, sim = _script_match(text)
    flags = _flag_hits(text)

    score = 1.0 - (1.0 - match_score) * math.prod(1.0 - e for e, _ in flags)

    reasons = []
    if match_score >= MATCH_CAP * 0.75:
        reasons.append(f"reads like a known {category} script (similarity {sim:.2f})")
    reasons += [reason for _, reason in sorted(flags, reverse=True)]
    if reasons:
        explanation = "Message: " + "; ".join(reasons)
    else:
        explanation = "Message doesn't resemble known scam scripts"

    return RiskSignal(signal_name="similarity", score=float(score), explanation=explanation)

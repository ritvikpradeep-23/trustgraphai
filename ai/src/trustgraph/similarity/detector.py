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
import json
import math
import os
import re

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion

from trustgraph.paths import model_path
from trustgraph.signal import RiskSignal
from trustgraph.similarity.corpus import LEGIT_MESSAGES, SCAM_SCRIPTS
from trustgraph.textnorm import normalize

# A promoted, larger example list (scripts/promote_model.py puts it here).
# Without the file, the built-in lists in corpus.py are used.
CORPUS_PATH = "models/similarity_corpus.json"

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
     r"|\b(read|send|tell|give|forward|share|confirm)\b.{0,40}\bcode\b.{0,40}\b(sent|texted|arrived|received)\b"
     # "download our support app and share the code": asking for the code itself.
     # Not "share your referral code" (another word sits between) or "share the code
     # with your friends", and not an offer: "I'll send the code later".
     r"|(?<!i'll )(?<!i will )(?<!we'll )(?<!we will )(?<!i can )"
     r"\b(read|send|tell|give|forward|share)\b (me |us )?(the|that|this|your) code\b"
     r"(?!\s+(with|to) (your |all your )?(friends|family|colleagues|classmates|team))"),
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
     r"\b(processing|release|clearance|administration|admin|withdrawal|handling|redelivery|storage|background[- ]check|"
     r"activation|onboarding|unlock(ing)?) (fee|tax|charge|deposit)s?\b"
     r"|\bpay\b.{0,40}\b(upfront|up front|in advance|before (you|your) (start|first day))\b"),
    # ---- Emotional-pressure rules (eval/emotional/). A family emergency is often real;
    # the tell is paying SOMEONE ELSE's account, or money demanded with guilt or a threat.
    (0.5, "asks you to pay someone else's account in an emergency",
     r"\b(send|transfer|pay|wire|gpay|venmo|zelle)\b.{0,40}\b(to|on|into|in|via) "
     # Anyone else's account: "his", "the man's", "my friend's", "the doctor's".
     r"(his|her|their|(the|this|that|my|a) \w+'s|the (doctor|nurse|lawyer|attorney|inspector|officer|receptionist|clinic|garage|police)) "
     r"(account|upi|gpay|zelle|venmo|cash ?app|paypal|number|wallet)\b"
     # Hinglish / Manglish: "unke UPI pe bhejo", "uske number pe GPay karo", "ee number il GPay cheyyu".
     r"|\b(unke|uske|unka|uska|inke|iske) (upi|number|account|gpay)\b.{0,15}\b(pe|par|me|mein)\b.{0,20}\b(bhej\w*|gpay|transfer|daal\w*|kar\w*)\b"
     r"|\bee (number|account)\b.{0,10}\b(il|ilekku)\b.{0,15}\b(gpay|ayakk\w*|cheyy\w*)\b"),
    (0.4, "asks for money inside an emergency story",
     r"\b(accident|crash(ed)?|hospital|icu|ambulance|surgery|operation|stitches|arrested|jail|bail|police station|"
     r"stranded|stuck at|deport\w*|fine of)\b.{0,160}"
     r"(\b(send|transfer|wire|pay|bhej\w*|gpay)\b.{0,40}(\$|£|€|₹|\brs\.?\b|\d|lakh|thousand|\baccount\b|\bupi\b|\bcash ?app\b|\bzelle\b|\bvenmo\b)"
     # The amount can come first: "they need 15,000 before the scan, please send it now".
     r"|(\$|£|€|₹|\brs\.?\s?)?\d[\d,.]*\s?(k|lakh|thousand)?\b.{0,60}\b(send|transfer|wire|pay|bhej\w*|gpay)\b"
     # Hinglish puts the account first: "is account pe bhej dijiye".
     r"|\b(account|upi)\b.{0,20}\b(bhej\w*|transfer)\b)"),
    # "New number" is common and honest; a new number plus a money ask is the classic "Hi Mum" scam.
    (0.5, "asks for money from a new or borrowed phone",
     r"\b(new number|naya number|friend'?s phone|mate'?s phone|someone else'?s phone|"
     r"(old |my )?phone (broke|died|smashed|got stolen|was stolen|is broken)|(lost|dropped|broke|smashed) my phone)\b.{0,200}"
     r"\b(pay|send|transfer|lend|bhej\w*)\b.{0,60}(\$|£|€|₹|\brs\.?\b|\d|lakh|\b(bill|invoice|rent|fee|account|payment)\b)"),
    (0.6, "pressures you with guilt, self-harm or a threat to pay",
     r"\b(if you don'?t|unless you)\b.{0,30}\b(send|pay|transfer)\b.{0,80}\b(myself|kill myself|hurt myself|what i'?ll do)\b"
     r"|\b(if you (ever |really )?(cared|loved|love)|you owe me)\b.{0,80}\b(send|pay|transfer)\b"
     r"|\b(send|pay|transfer)\b.{0,80}\b(if you (ever |really )?(cared|loved|love)( me)?|you owe me)\b"),
    # ---- Proposed rules A-H (reports/fast/proposed_rules.md), applied after review.
    (0.7, "asks for a PIN or approval to RECEIVE money",
     r"\b(scan|approve|accept|enter|type)\b.{0,60}\b(upi )?pin\b.{0,60}\b(receive|get|credit|refund|come back|aa jayenge|varum)\b"
     r"|\bapprove\b.{0,30}\b(the |this |my )?(incoming |payment |collect |upi )?request\b.{0,60}\b(receive|credit|refund|get it|back|reverse)"),
    (0.8, "asks you to run a command or script it copied for you",
     r"\b(run|paste|execute)\b.{0,50}\b(command|script|code|fix)\b.{0,50}\b(copied|clipboard)\b"
     r"|\b(copied|clipboard)\b.{0,50}\b(command|script|code)\b.{0,40}\b(run|paste|execute)\b"),
    (0.7, "asks to connect a wallet or share a recovery phrase",
     r"\b(connect|link)\b (your )?wallet\b|\b(recovery|seed) (phrase|words)\b|\bprivate key\b"),
    (0.7, "tells you to stay on a video call (\"digital arrest\")",
     r"\b(stay|remain|keep)\b (on )?(this|the) (video )?call\b|\bdo not (disconnect|cut|end) (the )?(video )?call\b"
     r"|\bkeep (the|your) (camera|video) on\b|\bdigital arrest\b"),
    # Only as a threat ("or I'll send it to your family"), not "share the code with your family too".
    (0.6, "threatens to contact your contacts, family or employer",
     r"(\bor\b|\bunless\b|\botherwise\b|\bi'?ll\b|\bi will\b|\bwe'?ll\b|\bwe will\b|\bgoing to\b).{0,30}"
     r"\b(message|call|contact|send|share|post|forward|tell)\b.{0,40}"
     r"\b(all |everyone in )?(your|ur) (contacts|contact list|family|employer|boss|office|wife|husband)\b"),
    (0.5, "asks you to pay to unlock, release or withdraw something",
     r"\b(pay|deposit|recharge|transfer)\b.{0,50}\bto (unlock|release|restore|withdraw|reactivate)\b"),
    (0.4, "threatens to cut a service or block an account today",
     r"\b(power|electricity|current|supply|account|sim|tag|fastag|licen[cs]e)\b.{0,40}"
     r"\b(cut|disconnected|suspended|blocked|blacklisted|deactivated|frozen)\b.{0,40}"
     r"\b(today|tonight|within \d+ hours|immediately|in \d+ hours)\b"),
    (0.4, "asks for a deposit or advance to hold a rental or booking",
     r"\b(deposit|token advance|holding fee|advance)\b.{0,60}\b(hold|block|reserve|secure|confirm)\b.{0,40}"
     r"\b(flat|room|apartment|villa|studio|pg|booking|it)\b"
     r"|\b(hold|block|reserve)\b.{0,30}\b(flat|room|apartment)\b.{0,60}\b(deposit|advance)\b"),
    # ---- Email rules (eval/email/, real phishing and advance-fee emails).
    # An honest provider may ask you to confirm details; phishing adds "or it gets closed".
    (0.5, "asks you to verify your account or lose it",
     r"\b(verify|confirm|validate|re-?validate|update|re-?activate|authenticate|upgrade|restore|unlock)\b.{0,60}"
     r"\b(e-?mail|mail ?box|web-?mail|account|password|log-?in|credentials|ownership|identity|(account|billing|personal) (details|information))\b.{0,250}"
     r"\b(suspend\w*|de-?activat\w*|disabled?|blocked|limited|restricted|expire[ds]?|terminated|closed|shut ?down|locked|deleted|cancell?ed|lose|loss of)\b"
     r"|\b(suspend\w*|de-?activat\w*|disabled|blocked|limited|restricted|expire[ds]?|terminated|shut ?down|locked)\b.{0,250}"
     r"\b(verify|confirm|validate|re-?validate|re-?activate|authenticate|upgrade|restore|unlock)\b.{0,60}"
     r"\b(e-?mail|mail ?box|web-?mail|account|password|log-?in|credentials|ownership|identity|(account|billing|personal) (details|information))\b"),
    (0.5, "says your mail is held or your mailbox is full, and asks you to click",
     r"\b((mail ?box|mail quota|e-?mail quota|storage|inbox)\b.{0,60}\b(full|exceeded|\d+ ?%|limit|running (out|low))"
     # No \b after this list: scraped emails run words together ("could not be deliveredThere are").
     r"|(messages?|e-?mails?|mails?)\b.{0,40}\b(pending|on hold|held|placed on hold|could not be delivered|undelivered|not delivered|delayed|stopped))"
     r".{0,300}\b(click|verify|confirm|validate|release|retrieve|upgrade|increase|log ?in|sign ?in)\b"),
    (0.4, "says your password or mailbox is about to expire, with a link to click",
     r"\b(password|mail ?box|e-?mail account|web-?mail|account)\b.{0,40}\b(will|is going to|is about to|about to)\b.{0,20}"
     r"\b(expire|be (suspended|deactivated|closed|deleted|shut ?down|disabled|blocked|terminated))\b.{0,200}"
     r"\b(click|check it out|here|link|below|button)\b"),
    (0.6, "offers you a share of a stranger's money (advance-fee fraud)",
     r"\b(next of kin|beneficiary|foreign (partner|account)|late (husband|father|client|mr|dr)|deceased|unclaimed|dormant|abandoned)\b.{0,400}"
     r"(\b(million|millions)\b|\bus\$|\busd\b|\$\s?\d|£\s?\d|€\s?\d)"
     r"|(\b(million|millions)\b|\bus\$|\busd\b|\$\s?\d|£\s?\d|€\s?\d).{0,400}"
     r"\b(next of kin|beneficiary|foreign (partner|account)|late (husband|father|client|mr|dr)|deceased|unclaimed|dormant|abandoned)\b"
     r"|\b\d{1,2} ?(%|percent|per cent)\b.{0,60}\b(of (the|this) (total )?(sum|fund|funds|money|amount))\b"),
    (0.5, "says you won a lottery, award or donation you never entered",
     r"\b(won|winner|winning|selected|awarded|chosen)\b.{0,100}\b(lottery|lotto|sweepstakes?|draw|award|prize|grant|donation|jackpot)\b.{0,300}"
     r"\b(claim|contact|fill|send|processing|reply|payment)\b"),
]
_FLAGS = [(e, reason, re.compile(p, re.IGNORECASE | re.DOTALL)) for e, reason, p in RED_FLAGS]

# "Never share this code", "we will never ask you to move money", "the bank
# never asks for your PIN": honest messages warn about exactly the asks
# scammers make. Covers every form of the verb (ask, asks, asked, asking).
# The "never" can sit right before the flagged words ("Never share your
# password") or before an earlier verb ("never ask you to share your password").
_NEGATION = re.compile(
    r"\b(never|will not|won'?t|do not|don'?t|does not|doesn'?t|must not|mustn'?t|should not|shouldn'?t)\s+"
    r"((ask|share|give|send|tell|move|transfer|request|disclose|charge)(s|es|ed|ing)?\b"
    # "Don't tell anyone, send me the code" is a secrecy demand, not a warning.
    r"(?!\s+(anyone|anybody|your (family|bank|wife|husband)|the (bank|branch|police)|police|mum|mom|dad))"
    r"[^.!?]{0,40})?$",
    re.IGNORECASE)
# Hinglish and Manglish put the "don't" after the verb: "share na karein",
# "share mat karo", "share cheyyaruthu" (Malayalam: must not do), "share cheyyalle".
# "mat share karo" puts it before.
_NEGATION_AFTER = re.compile(
    r"\w+\s+(na|nahi|nahin|mat|cheyyaruth\w*|cheyyall?e|cheyyenda|cheyyathe)\b(?!\s*\?)",  # "share na?" asks, not forbids
    re.IGNORECASE)
_NEGATION_BEFORE = re.compile(r"\b(mat|kabhi (bhi )?(na|nahi|nahin))\s+$", re.IGNORECASE)


def _negated(text: str, start: int) -> bool:
    before = text[:start]
    return bool(_NEGATION.search(before) or _NEGATION_BEFORE.search(before) or _NEGATION_AFTER.match(text, start))


_WORD_START = re.compile(r"\b\w")


def _flag_hits(text: str) -> list[tuple[float, str]]:
    hits = []
    for evidence, reason, pattern in _FLAGS:
        if not pattern.search(text):
            continue
        # Try every word the ask could start at, not just the first match: in
        # "Share na? Send me the code" the first candidate looks negated, the second isn't.
        starts = (m.start() for m in _WORD_START.finditer(text))
        if any(pattern.match(text, i) and not _negated(text, i) for i in starts):
            hits.append((evidence, reason))
    return hits


_index = None


def build_index(scam_scripts: dict[str, list[str]], legit_messages: list[str], normalized: bool = False) -> dict:
    """Fit the TF-IDF index on a reference corpus. The live signal uses the
    built-in corpus (or a promoted one); experiments pass modified copies.
    normalized=True compares texts after trustgraph.textnorm.normalize
    (disguise tricks undone, links/phones/amounts/numbers as markers)."""
    prep = normalize if normalized else (lambda t: t)
    scam_texts, scam_labels = [], []
    for category, texts in scam_scripts.items():
        scam_texts += [prep(t) for t in texts]
        scam_labels += [category] * len(texts)
    legit_texts = [prep(t) for t in legit_messages]
    vectorizer = FeatureUnion([
        ("words", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)),
        ("chars", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)),
    ])
    vectorizer.fit(scam_texts + legit_texts)
    return {
        "vectorizer": vectorizer,
        "scam": vectorizer.transform(scam_texts),
        "scam_labels": scam_labels,
        "legit": vectorizer.transform(legit_texts),
        "normalized": normalized,
    }


def load_corpus(path: str | None = None) -> tuple[dict[str, list[str]], list[str], bool]:
    """(scam scripts, legit messages, normalized) from a promoted file (in
    TRUSTGRAPH_MODEL_DIR or models/), else the built-ins."""
    path = path or model_path("similarity_corpus.json")
    if not os.path.exists(path):
        return SCAM_SCRIPTS, LEGIT_MESSAGES, False
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data["scam_scripts"], data["legit_messages"], bool(data.get("normalized", False))


def _build_index():
    global _index
    if _index is None:
        _index = build_index(*load_corpus())
    return _index


def _cosine_max(query, matrix) -> tuple[float, int]:
    # FeatureUnion concatenates two L2-normalized blocks, so each row has norm sqrt(2).
    sims = (matrix @ query.T).toarray().ravel() / 2.0
    best = int(np.argmax(sims))
    return float(sims[best]), best


def _script_match(text: str) -> tuple[float, str | None, float]:
    index = _build_index()
    query = index["vectorizer"].transform([normalize(text) if index.get("normalized") else text])
    scam_sim, best = _cosine_max(query, index["scam"])
    legit_sim, _ = _cosine_max(query, index["legit"])
    if scam_sim < MIN_SCAM_SIMILARITY:
        return 0.0, None, scam_sim
    score = 1.0 / (1.0 + math.exp(-((scam_sim - legit_sim) - MARGIN_MID) / MARGIN_SCALE))
    return min(score, MATCH_CAP), index["scam_labels"][best], scam_sim


def components(text: str) -> tuple[float, str | None, float, list[tuple[float, str]], float]:
    """(wording-match score, closest scam category, its similarity, red flags, combined score)."""
    match_score, category, sim = _script_match(text)
    flags = _flag_hits(text)
    score = 1.0 - (1.0 - match_score) * math.prod(1.0 - e for e, _ in flags)
    return match_score, category, sim, flags, score


def similarity_score(interaction: dict) -> RiskSignal:
    text = interaction.get("message_text")
    if not isinstance(text, str) or not text.strip():
        return RiskSignal(signal_name="similarity", score=0.0, explanation="No message text to compare")
    text = " ".join(text.split())[:MAX_CHARS]
    match_score, category, sim, flags, score = components(text)

    reasons = []
    if match_score >= MATCH_CAP * 0.75:
        reasons.append(f"reads like a known {category} script (similarity {sim:.2f})")
    reasons += [reason for _, reason in sorted(flags, reverse=True)]
    if reasons:
        explanation = "Message: " + "; ".join(reasons)
    else:
        explanation = "Message doesn't resemble known scam scripts"

    return RiskSignal(signal_name="similarity", score=float(score), explanation=explanation)

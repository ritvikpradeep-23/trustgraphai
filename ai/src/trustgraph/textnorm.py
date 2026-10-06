"""Normalize message text before a model compares or learns from it.

Two jobs, applied the same way to scam and honest messages:

1. Undo disguise tricks, so a disguised message looks like the plain one:
   spaced-out letters ("u r g e n t"), digits for letters ("upd4te"),
   broken links ("pay[.]example.com", "hxxp://", " dot "), line splits and
   capitals.
2. Replace details that say nothing about scams with one marker each: every
   link becomes "zzlink", phone numbers "zzphone", money amounts "zzamount",
   codes and other numbers "zznum". In the training data, scam and honest
   links were written in different styles; without this a model could learn
   the style instead of the scam.

Markers are plain words (no brackets) so the TF-IDF tokenizer keeps them whole.
"""
import re

MARKERS = {"zzlink": "<link>", "zzphone": "<phone>", "zzamount": "<amount>", "zznum": "<number>"}

_SPACED = re.compile(r"\b(?:\w ){2,}\w\b")  # "u r g e n t" (3+ single characters)
_URL = re.compile(
    r"\[link\]|(?:https?|hxxps?)://\S+|\bwww\.\S+"
    r"|\b[\w-]+(?:\.[\w-]+)*\.(?:com|org|net|in|uk|co|io|test|invalid|example|link|xyz|top)\b(?:/\S*)?",
    re.IGNORECASE)
_PHONE = re.compile(r"\[phone\]|\+?\d[\d -]{8,}\d", re.IGNORECASE)
_AMOUNT = re.compile(r"(?:rs\.?|inr|₹|£|\$|€|usd|eur|gbp)\s?\d[\d,]*(?:\.\d+)?(?:\s?(?:lakh|lakhs|k|crore))?"
                     r"|\b\d[\d,]*(?:\.\d+)?\s?(?:rupees|pounds|dollars|euros|usdt|btc)\b", re.IGNORECASE)
_LEET_WORD = re.compile(r"\b(?=\w*[a-z])(?=\w*[0134])[a-z0134]{3,}\b")
_CODE = re.compile(r"\b(?:[a-z]{2,4}-)?\d+\b")


def _unleet(m: re.Match) -> str:
    return m.group(0).translate(str.maketrans("0134", "oiea"))


def normalize(text: str) -> str:
    text = text.lower().replace("[.]", ".").replace(" dot ", ".").replace("hxxp", "http")
    text = _SPACED.sub(lambda m: m.group(0).replace(" ", ""), text)
    text = _URL.sub(" zzlink ", text)
    text = _PHONE.sub(" zzphone ", text)
    text = _AMOUNT.sub(" zzamount ", text)
    text = _LEET_WORD.sub(_unleet, text)
    text = _CODE.sub(" zznum ", text)
    return " ".join(text.split())


def readable(term: str) -> str:
    """Show markers as <link> etc. in explanations."""
    for marker, label in MARKERS.items():
        term = term.replace(marker, label)
    return term

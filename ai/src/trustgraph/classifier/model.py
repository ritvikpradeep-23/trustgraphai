"""The text classifier's model: TF-IDF features and logistic regression.

Kept deliberately simple so every part can be inspected:
  1. text is normalized (trustgraph.textnorm): disguise tricks undone, links,
     phones, amounts and numbers replaced by markers, the same for both labels
  2. features: word 1-2 grams plus character 3-5 grams (TF-IDF)
  3. logistic regression with balanced class weights (scams are the minority)
  4. Platt scaling: a one-feature logistic fit on out-of-fold raw scores turns
     the raw score into a probability-like number between 0 and 1
"""
import re

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion

from trustgraph.textnorm import normalize


def make_vectorizer() -> FeatureUnion:
    return FeatureUnion([
        ("words", TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=2)),
        ("chars", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True, min_df=2)),
    ])


def prepare(text: str, removed: tuple[str, ...] = ()) -> str:
    """Normalize, then drop any words the shortcut audit removed."""
    text = normalize(text)
    if removed:
        text = re.sub(r"\b(" + "|".join(map(re.escape, removed)) + r")\b", " ", text)
    return " ".join(text.split())


def _fit_once(texts: list[str], y: np.ndarray, c: float, seed: int):
    vec = make_vectorizer().fit(texts)
    lr = LogisticRegression(C=c, class_weight="balanced", max_iter=5000, solver="liblinear", random_state=seed)
    lr.fit(vec.transform(texts), y)
    return vec, lr


def fit(raw_texts: list[str], y: np.ndarray, c: float, folds: list, removed: tuple[str, ...] = (),
        seed: int = 0) -> dict:
    """Train on all given texts. Platt scaling is fitted on out-of-fold raw
    scores from the given (group-aware) folds, so it never sees a score the
    model produced for its own training message."""
    texts = [prepare(t, removed) for t in raw_texts]
    oof = np.zeros(len(texts))
    for train, val in folds:
        vec, lr = _fit_once([texts[i] for i in train], y[train], c, seed)
        oof[val] = lr.decision_function(vec.transform([texts[i] for i in val]))
    platt = LogisticRegression(C=1e6, max_iter=1000).fit(oof.reshape(-1, 1), y)
    vec, lr = _fit_once(texts, y, c, seed)
    return {"vectorizer": vec, "model": lr, "platt": (float(platt.coef_[0, 0]), float(platt.intercept_[0])),
            "removed": tuple(removed), "c": c, "fusion_weight": 1.0}


def raw_scores(bundle: dict, raw_texts: list[str]) -> np.ndarray:
    texts = [prepare(t, bundle["removed"]) for t in raw_texts]
    return bundle["model"].decision_function(bundle["vectorizer"].transform(texts))


def scores(bundle: dict, raw_texts: list[str]) -> np.ndarray:
    a, b = bundle["platt"]
    return 1.0 / (1.0 + np.exp(-(a * raw_scores(bundle, raw_texts) + b)))


def feature_names(bundle: dict) -> list[tuple[str, str]]:
    """(block, term) for every feature, in coefficient order."""
    out = []
    for block, vec in bundle["vectorizer"].transformer_list:
        out += [(block, t) for t in vec.get_feature_names_out()]
    return out


def top_terms(bundle: dict, raw_text: str, k: int = 3) -> list[str]:
    """Words or phrases in this message that pushed the score up most
    (word features only: character fragments aren't readable)."""
    x = bundle["vectorizer"].transform([prepare(raw_text, bundle["removed"])]).tocsr()
    coef = bundle["model"].coef_[0]
    names = feature_names(bundle)
    contrib = [(x[0, j] * coef[j], names[j][1]) for j in x.indices if names[j][0] == "words" and coef[j] > 0]
    return [t for _, t in sorted(contrib, reverse=True)[:k]]

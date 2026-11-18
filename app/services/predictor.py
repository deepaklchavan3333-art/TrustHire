import hashlib, re, html
from pathlib import Path
import joblib

MAX_FIELD = 10000
FIELDS = ("title", "location", "company_profile", "description", "requirements", "benefits", "employment_type")
_RED_FLAGS = [
    ("upfront payment", r"registration fee|upfront fee|pay (a |the )?(fee|deposit)|payment to start|training fee"),
    ("unrealistic salary", r"earn\s*[$₹]?\s?\d{4,}|\d{3,}\s?(per month|/month)"),
    ("no experience required", r"no experience (needed|required)|no experience necessary"),
    ("urgency pressure", r"act now|immediate hiring|urgent hiring|limited slots"),
    ("free email contact", r"@(gmail|yahoo|hotmail|outlook)\.com"),
]
class Predictor:
    def __init__(self, path):
        self.pipeline = joblib.load(path) if Path(path).exists() else None
        self.version = "trained-pipeline" if self.pipeline else "rules-fallback-v1"
    def predict(self, fields):
        text = " ".join(str(fields.get(k, "")) for k in FIELDS)
        if len(text) > MAX_FIELD * len(FIELDS): raise ValueError("Posting is too long.")
        clean = html.unescape(re.sub(r"<[^>]*>", " ", text)).lower()
        flags = [name for name, pat in _RED_FLAGS if re.search(pat, clean)]
        if self.pipeline:
            probability = float(self.pipeline.predict_proba([clean])[0][1])
            label = "fake" if probability >= .5 else "genuine"
            signals = flags[:3] or ["language patterns in the posting", "posting details", "model text features"]
        else:
            # Transparent demonstration heuristic; replace with ml/train.py artifact for ML scoring.
            probability = min(.97, .08 + .27 * len(flags) + (.15 if not fields.get("company_profile", "").strip() else 0))
            label = "fake" if probability >= .5 else "genuine"
            signals = flags[:3] + (["missing company profile"] if not fields.get("company_profile", "").strip() else [])
            signals = signals[:3] or ["No common red-flag phrases detected", "Review employer identity", "Verify the role independently"]
        return {"label": label, "probability_fake": round(probability, 4), "confidence": round((probability if label == "fake" else 1-probability)*100, 1), "top_signals": signals, "red_flags": flags, "model_version": self.version}

def text_hash(fields):
    return hashlib.sha256("\x1f".join(str(fields.get(k, "")).strip() for k in FIELDS).encode()).hexdigest()

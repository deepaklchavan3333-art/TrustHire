import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-me")
    DATABASE = os.environ.get("DATABASE", str(BASE_DIR / "data" / "predictions.sqlite"))
    MODEL_PATH = os.environ.get("MODEL_PATH", str(BASE_DIR / "models" / "job_model.joblib"))
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

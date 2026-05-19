from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "database" / "app.db"
UPLOAD_DIR = BASE_DIR / "database" / "uploads"

# Try to use local model only when available.
TRANSFORMERS_MODEL = "j-hartmann/emotion-english-distilroberta-base"

import os
from pathlib import Path
from dotenv import load_dotenv

# Project root = one level above /app
BASE_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = BASE_DIR / ".env"

# Force load .env from absolute path
load_dotenv(dotenv_path=ENV_FILE)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/")

if not OPENAI_API_KEY:
    raise RuntimeError(f"OPENAI_API_KEY missing. Looked in: {ENV_FILE}")
if not PUBLIC_BASE_URL:
    raise RuntimeError(f"PUBLIC_BASE_URL missing. Looked in: {ENV_FILE}")
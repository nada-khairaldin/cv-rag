import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def required(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing {name} in .env")
    return value



POSTGRES_HOST = "localhost"
POSTGRES_PORT = int(required("POSTGRES_PORT"))
POSTGRES_DB = "cvrag"
POSTGRES_USER = "cvrag"
POSTGRES_PASSWORD = required("POSTGRES_PASSWORD")

# Google Drive
DRIVE_FOLDER_ID = required("DRIVE_FOLDER_ID")
GOOGLE_APPLICATION_CREDENTIALS = str(BASE_DIR / required("GOOGLE_APPLICATION_CREDENTIALS"))


GEMINI_API_KEY = required("GEMINI_API_KEY")
EMBEDDING_MODEL = "gemini-embedding-2"
EMBEDDING_DIM = 1536

# LlamaParse (optional: only needed when comparing parsers)
LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY", "")
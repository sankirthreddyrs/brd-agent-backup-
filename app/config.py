import os
from dotenv import load_dotenv

load_dotenv()

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us-central1")
GCS_BUCKET = os.getenv("GCS_BUCKET", "")
BQ_DATASET = os.getenv("BQ_DATASET", "brd_agent")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() in ("true", "1", "yes")

DEMO_DATA_DIR = os.getenv("DEMO_DATA_DIR", "demo/data")
DEMO_CACHE_DIR = os.getenv("DEMO_CACHE_DIR", "demo/cache")

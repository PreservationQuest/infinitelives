"""Configuration for the Gameplay Event Agent - OpenAI API."""
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-2024-08-06")
NEOSEEKER_RATE_LIMIT = float(os.getenv("NEOSEEKER_RATE_LIMIT", "2.0"))
SCRAPE_MAX_PAGES = int(os.getenv("SCRAPE_MAX_PAGES", "10"))
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

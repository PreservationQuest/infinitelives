"""Configuration for the Gameplay Event Agent - Claude API."""
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
NEOSEEKER_RATE_LIMIT = float(os.getenv("NEOSEEKER_RATE_LIMIT", "2.0"))
SCRAPE_MAX_PAGES = int(os.getenv("SCRAPE_MAX_PAGES", "10"))
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
CACHE_DIR = DATA_DIR / "cache"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

"""Configuration."""
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

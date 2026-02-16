"""
Configuration management with validation and security best practices.
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    """Application configuration with validation."""
    
    # OpenAI Settings
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    OPENAI_ORG_ID: str = os.getenv('OPENAI_ORG_ID', '')
    MODEL_NAME: str = os.getenv('MODEL_NAME', 'gpt-4o-2024-08-06')
    
    # Assistant Settings
    ASSISTANT_ID: Optional[str] = os.getenv('ASSISTANT_ID') or None
    VECTOR_STORE_NAME: str = "Video Game Research"
    
    # Application Settings
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    MAX_RETRIES: int = int(os.getenv('MAX_RETRIES', '3'))
    REQUEST_TIMEOUT: int = int(os.getenv('REQUEST_TIMEOUT', '60'))
    
    # File Paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    DATA_DIR: Path = PROJECT_ROOT / "data"
    DOCS_DIR: Path = PROJECT_ROOT / "docs"
    LOGS_DIR: Path = PROJECT_ROOT / "logs"
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        errors = []
        
        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is required")
        elif not cls.OPENAI_API_KEY.startswith('sk-'):
            errors.append("OPENAI_API_KEY appears invalid (should start with 'sk-')")
            
        if not cls.OPENAI_ORG_ID:
            errors.append("OPENAI_ORG_ID is required")
        elif not cls.OPENAI_ORG_ID.startswith('org-'):
            errors.append("OPENAI_ORG_ID appears invalid (should start with 'org-')")
        
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            raise ValueError(error_msg)
        
        logger.info("Configuration validated successfully")
    
    @classmethod
    def setup_directories(cls) -> None:
        """Create necessary directories."""
        for directory in [cls.DATA_DIR, cls.LOGS_DIR]:
            directory.mkdir(parents=True, exist_ok=True)


# Validate on import
try:
    Config.validate()
    Config.setup_directories()
except ValueError as e:
    logger.error(f"Configuration error: {e}")
    logger.info("Please copy .env.example to .env and fill in your credentials")
    raise

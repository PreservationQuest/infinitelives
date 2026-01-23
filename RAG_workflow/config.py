import os
from dotenv import load_dotenv

load_dotenv()

# Get API credentials
OPENAI_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_ORG = os.getenv('OPENAI_ORG_ID')
MODEL_NAME = os.getenv('MODEL_NAME', 'gpt-4o-2024-08-06')

# Validation
if not OPENAI_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

if not OPENAI_ORG:
    raise ValueError("OPENAI_ORG_ID not found in environment variables")

print(f"✓ Config loaded: {OPENAI_KEY[:10]}...{OPENAI_KEY[-4:]}")
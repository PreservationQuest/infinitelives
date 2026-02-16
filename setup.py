#!/usr/bin/env python3
"""
Quick setup script for Infinite Lives v2.
"""
import os
import sys
from pathlib import Path


def create_env_file():
    """Create .env file from template if it doesn't exist."""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if not env_example.exists():
        print("❌ .env.example not found")
        return False
    
    # Copy template
    env_file.write_text(env_example.read_text())
    print("✅ Created .env file from template")
    print("\n⚠️  IMPORTANT: Edit .env and add your OpenAI credentials:")
    print("   - OPENAI_API_KEY")
    print("   - OPENAI_ORG_ID")
    return False


def check_dependencies():
    """Check if required packages are installed."""
    required = ["openai", "pandas", "dotenv"]
    missing = []
    
    for package in required:
        try:
            __import__(package if package != "dotenv" else "dotenv")
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        print("\nInstall with: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies installed")
    return True


def create_directories():
    """Create necessary directories."""
    dirs = ["data", "docs", "logs", "data/cache"]
    
    for dir_name in dirs:
        Path(dir_name).mkdir(parents=True, exist_ok=True)
    
    print("✅ Created necessary directories")
    return True


def check_documents():
    """Check for reference documents."""
    docs_dir = Path("docs")
    doc_files = list(docs_dir.glob("*.docx")) + list(docs_dir.glob("*.pdf"))
    
    if not doc_files:
        print("⚠️  No documents found in docs/")
        print("   Add reference documents (Detailed_Instructions.docx, etc.)")
        return False
    
    print(f"✅ Found {len(doc_files)} reference document(s)")
    return True


def validate_env():
    """Validate .env configuration."""
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ["OPENAI_API_KEY", "OPENAI_ORG_ID"]
    missing = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value or "your_" in value.lower():
            missing.append(var)
    
    if missing:
        print(f"❌ Missing or invalid environment variables: {', '.join(missing)}")
        print("\nEdit .env and set these values")
        return False
    
    print("✅ Environment variables configured")
    return True


def setup_assistant():
    """Setup the OpenAI assistant."""
    try:
        from src import AssistantManager
        
        print("\n🚀 Setting up assistant...")
        manager = AssistantManager()
        assistant_id = manager.get_or_create_assistant()
        
        print(f"\n✅ Assistant ready: {assistant_id}")
        
        # Check if ASSISTANT_ID is in .env
        env_file = Path(".env")
        env_content = env_file.read_text()
        
        if f"ASSISTANT_ID={assistant_id}" not in env_content:
            print("\n💡 Add this to your .env file:")
            print(f"ASSISTANT_ID={assistant_id}")
        
        return True
    
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        return False


def main():
    """Run setup process."""
    print("=" * 60)
    print("Infinite Lives v2.0 - Setup")
    print("=" * 60)
    print()
    
    # Step 1: Create .env
    print("Step 1: Configuration")
    needs_env_edit = not create_env_file()
    print()
    
    if needs_env_edit:
        print("⏸️  Please edit .env with your credentials, then run this script again")
        return 1
    
    # Step 2: Check dependencies
    print("Step 2: Dependencies")
    if not check_dependencies():
        return 1
    print()
    
    # Step 3: Validate environment
    print("Step 3: Validate Configuration")
    if not validate_env():
        return 1
    print()
    
    # Step 4: Create directories
    print("Step 4: Directory Structure")
    create_directories()
    print()
    
    # Step 5: Check documents
    print("Step 5: Reference Documents")
    check_documents()
    print()
    
    # Step 6: Setup assistant
    print("Step 6: Assistant Setup")
    if not setup_assistant():
        return 1
    print()
    
    # Success
    print("=" * 60)
    print("✅ Setup Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Process a dataset: python -m src.main process input.csv -o output.csv")
    print("  2. Interactive queries: python -m src.main query")
    print("  3. See examples: python examples.py")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
Command-line interface for Infinite Lives RAG system.
"""
import sys
import argparse
from pathlib import Path

from .logging_config import setup_logging, get_logger
from .processor import GameResearchProcessor
from .assistant import AssistantManager

logger = get_logger(__name__)


def process_dataset(args):
    """Process a dataset CSV file."""
    setup_logging()
    logger.info("Starting dataset processing...")
    
    processor = GameResearchProcessor(use_verification=args.verify)
    
    try:
        result_df = processor.process_dataset(
            input_csv=args.input,
            output_csv=args.output
        )
        logger.info(f"Processing complete. Processed {len(result_df)} papers.")
        return 0
    
    except Exception as e:
        logger.error(f"Processing failed: {e}", exc_info=True)
        return 1


def query_assistant(args):
    """Interactive query mode."""
    setup_logging()
    logger.info("Starting interactive query mode...")
    
    processor = GameResearchProcessor()
    
    print("\n🎮 Infinite Lives - Video Game Research Assistant")
    print("=" * 60)
    print("Ask questions about video game research.")
    print("Type 'quit' or 'exit' to stop.\n")
    
    while True:
        try:
            question = input("You: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not question:
                continue
            
            print("\nAssistant: ", end="", flush=True)
            response = processor.simple_query(question)
            print(response)
            print()
        
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        
        except Exception as e:
            logger.error(f"Query failed: {e}")
            print(f"\nError: {e}\n")
    
    return 0


def setup_assistant(args):
    """Setup or reset the assistant."""
    setup_logging()
    
    manager = AssistantManager()
    
    if args.reset:
        logger.info("Resetting assistant...")
        manager.cleanup()
        print("Assistant deleted. Run setup again to create a new one.")
        return 0
    
    logger.info("Setting up assistant...")
    assistant_id = manager.get_or_create_assistant()
    print(f"\n✅ Assistant ready: {assistant_id}")
    print(f"\nAdd this to your .env file:")
    print(f"ASSISTANT_ID={assistant_id}")
    
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Infinite Lives - Video Game Research RAG System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Setup assistant
  python -m src.main setup
  
  # Process dataset
  python -m src.main process input.csv -o output.csv
  
  # Process with verification (slower, more accurate)
  python -m src.main process input.csv -o output.csv --verify
  
  # Interactive queries
  python -m src.main query
  
  # Reset assistant
  python -m src.main setup --reset
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Setup or reset assistant')
    setup_parser.add_argument('--reset', action='store_true', help='Delete existing assistant')
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Process dataset')
    process_parser.add_argument('input', help='Input CSV file')
    process_parser.add_argument('-o', '--output', help='Output CSV file')
    process_parser.add_argument('--verify', action='store_true', 
                               help='Enable two-pass verification (slower)')
    
    # Query command
    query_parser = subparsers.add_parser('query', help='Interactive query mode')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == 'setup':
            return setup_assistant(args)
        elif args.command == 'process':
            return process_dataset(args)
        elif args.command == 'query':
            return query_assistant(args)
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 130
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())

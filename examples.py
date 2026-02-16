"""
Simple usage examples for Infinite Lives RAG system.
"""
from src import GameResearchProcessor, AssistantManager


def example_simple_query():
    """Example: Simple one-off query."""
    processor = GameResearchProcessor()
    
    question = "What are common game mechanics studied in behavioral research?"
    response = processor.simple_query(question)
    print(f"Q: {question}")
    print(f"A: {response}\n")


def example_process_single_paper():
    """Example: Process a single paper."""
    processor = GameResearchProcessor()
    
    paper_data = {
        "ID": "paper_001",
        "Abstract": "This study examines the effects of video game violence...",
        "Introduction": "Research has shown various impacts...",
        "Methods": "We conducted a survey with 200 participants...",
        "Conclusion": "Results indicate moderate correlation..."
    }
    
    results = processor.process_paper(
        paper_data=paper_data,
        category="Behavioral",
        output_format="JSON with keys: findings, methodology, games_studied"
    )
    
    print("Processed sections:")
    for section, content in results.items():
        print(f"  {section}: {content[:100]}...")


def example_batch_processing():
    """Example: Process CSV dataset."""
    processor = GameResearchProcessor(use_verification=False)
    
    # Process dataset
    results = processor.process_dataset(
        input_csv="data/input.csv",
        output_csv="data/output.csv"
    )
    
    print(f"Processed {len(results)} papers")
    print(results.head())


def example_assistant_management():
    """Example: Manage assistant lifecycle."""
    manager = AssistantManager()
    
    # Get or create assistant
    assistant_id = manager.get_or_create_assistant()
    print(f"Assistant ID: {assistant_id}")
    
    # Query
    response = manager.query("What is the purpose of this assistant?")
    print(f"Response: {response}")
    
    # With verification
    verified_response = manager.query_with_verification(
        content="List game mechanics from uploaded documents",
        instructions="Format as bullet points"
    )
    print(f"Verified: {verified_response}")


if __name__ == "__main__":
    print("=" * 60)
    print("Infinite Lives - Usage Examples")
    print("=" * 60)
    
    print("\n1. Simple Query")
    print("-" * 60)
    example_simple_query()
    
    print("\n2. Process Single Paper")
    print("-" * 60)
    example_process_single_paper()
    
    print("\n3. Assistant Management")
    print("-" * 60)
    example_assistant_management()
    
    # Uncomment to run batch processing
    # print("\n4. Batch Processing")
    # print("-" * 60)
    # example_batch_processing()

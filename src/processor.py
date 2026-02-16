"""
RAG processor for video game research with batch processing and caching.
"""
import logging
import pandas as pd
from typing import List, Dict, Optional
from pathlib import Path
import json
from datetime import datetime

from .assistant import AssistantManager
from .config import Config

logger = logging.getLogger(__name__)


class GameResearchProcessor:
    """Process video game research papers with RAG."""
    
    SECTIONS = ["Abstract", "Introduction", "Methods", "Conclusion"]
    
    def __init__(self, use_verification: bool = False):
        """
        Initialize processor.
        
        Args:
            use_verification: Enable two-pass verification (slower but more accurate)
        """
        self.assistant = AssistantManager()
        self.use_verification = use_verification
        self.cache_dir = Config.DATA_DIR / "cache"
        self.cache_dir.mkdir(exist_ok=True)
    
    def process_paper(
        self,
        paper_data: Dict,
        category: str,
        output_format: str
    ) -> Dict:
        """
        Process a single paper section.
        
        Args:
            paper_data: Dictionary with paper content
            category: Subject category (e.g., "Behavioral", "Psychological")
            output_format: Expected output format template
        
        Returns:
            Processed data dictionary
        """
        paper_id = paper_data.get("ID", "unknown")
        results = {}
        
        for section in self.SECTIONS:
            content = paper_data.get(section, "")
            
            # Skip empty sections
            if not content or str(content).lower() in ["nan", "[nan]", ""]:
                logger.debug(f"Skipping empty section: {section}")
                continue
            
            # Build query
            query = self._build_query(section, category, content, output_format)
            
            # Process with or without verification
            try:
                if self.use_verification:
                    response = self.assistant.query_with_verification(
                        content=query,
                        instructions=f"Return response in format: {output_format}"
                    )
                else:
                    response = self.assistant.query(
                        content=query,
                        instructions=f"Return response in format: {output_format}",
                        temperature=0.0
                    )
                
                results[section] = response
                logger.info(f"Processed {paper_id} - {section}")
            
            except Exception as e:
                logger.error(f"Failed to process {paper_id} - {section}: {e}")
                results[section] = {"error": str(e)}
        
        return results
    
    def _build_query(
        self,
        section: str,
        category: str,
        content: str,
        output_format: str
    ) -> str:
        """Build the query prompt."""
        return (
            f"Paper section: {section}\n"
            f"Category: {category}\n"
            f"Content:\n{content}\n\n"
            f"Extract structured information according to the output format. "
            f"Focus on game mechanics, player effects, and research findings."
        )
    
    def process_dataset(
        self,
        input_csv: str,
        output_csv: str = None
    ) -> pd.DataFrame:
        """
        Process entire dataset from CSV.
        
        Args:
            input_csv: Path to input CSV file
            output_csv: Optional path to save results
        
        Returns:
            DataFrame with processed results
        """
        logger.info(f"Loading dataset: {input_csv}")
        df = pd.read_csv(input_csv)
        
        # Prepare results storage
        results = []
        
        # Process each row
        for idx, row in df.iterrows():
            paper_id = row.get("ID", idx)
            logger.info(f"Processing paper {idx + 1}/{len(df)}: {paper_id}")
            
            # Get category (first if semicolon-separated)
            category = str(row.get("Subject of Effect", "General"))
            if ";" in category:
                category = category.split(";")[0].strip()
            
            # Process paper
            paper_data = row.to_dict()
            processed = self.process_paper(
                paper_data=paper_data,
                category=category,
                output_format="JSON with keys: game_names, effects, metrics, findings"
            )
            
            # Combine results
            result_row = row.to_dict()
            result_row["processed_sections"] = json.dumps(processed)
            results.append(result_row)
            
            # Save checkpoint every 10 papers
            if (idx + 1) % 10 == 0:
                self._save_checkpoint(results, output_csv)
        
        # Create result DataFrame
        result_df = pd.DataFrame(results)
        
        # Save final results
        if output_csv:
            result_df.to_csv(output_csv, index=False)
            logger.info(f"Results saved to: {output_csv}")
        
        return result_df
    
    def _save_checkpoint(self, results: List[Dict], output_path: str = None):
        """Save processing checkpoint."""
        checkpoint_path = self.cache_dir / f"checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(checkpoint_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Checkpoint saved: {checkpoint_path}")
    
    def load_checkpoint(self, checkpoint_path: str) -> List[Dict]:
        """Load results from checkpoint."""
        with open(checkpoint_path, 'r') as f:
            return json.load(f)
    
    def simple_query(self, question: str) -> str:
        """
        Simple one-off query to the assistant.
        
        Args:
            question: Natural language question
        
        Returns:
            Assistant's response
        """
        return self.assistant.query(question, temperature=0.3)

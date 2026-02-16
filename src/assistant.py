"""
Assistant manager that handles creation, caching, and lifecycle.
"""
import logging
from typing import Optional, List
from pathlib import Path

from .config import Config
from .client import client

logger = logging.getLogger(__name__)


class AssistantManager:
    """Manages OpenAI assistants with caching and reuse."""
    
    INSTRUCTIONS = (
        "You are a gaming design data analyst specializing in video game research. "
        "Your role is to analyze research papers on video games and extract structured information. "
        "You must follow the exact output format provided in instructions and reference the "
        "Video Game Attributes document when categorizing games."
    )
    
    def __init__(self):
        self.assistant_id: Optional[str] = Config.ASSISTANT_ID
        self.vector_store_id: Optional[str] = None
    
    def get_or_create_assistant(self) -> str:
        """Get existing assistant or create new one."""
        # Use cached ID from config
        if self.assistant_id:
            try:
                assistant = client.get_assistant(self.assistant_id)
                logger.info(f"Using existing assistant: {self.assistant_id}")
                return self.assistant_id
            except Exception as e:
                logger.warning(f"Cached assistant not found: {e}")
                self.assistant_id = None
        
        # Try to find existing assistant by name
        assistants = client.list_assistants()
        for assistant in assistants:
            if assistant.name == Config.VECTOR_STORE_NAME:
                self.assistant_id = assistant.id
                logger.info(f"Found existing assistant: {self.assistant_id}")
                return self.assistant_id
        
        # Create new assistant
        logger.info("Creating new assistant...")
        self.assistant_id = self._create_new_assistant()
        
        # Save to config for future use
        logger.info(f"💡 Add this to your .env file:\nASSISTANT_ID={self.assistant_id}")
        
        return self.assistant_id
    
    def _create_new_assistant(self) -> str:
        """Create new assistant with vector store."""
        # Create assistant
        assistant_id = client.create_assistant(
            name=Config.VECTOR_STORE_NAME,
            instructions=self.INSTRUCTIONS,
            tools=[{"type": "file_search"}]
        )
        
        # Create vector store
        vector_store_id = client.create_vector_store(Config.VECTOR_STORE_NAME)
        self.vector_store_id = vector_store_id
        
        # Upload documents if they exist
        docs_dir = Config.DOCS_DIR
        if docs_dir.exists():
            doc_files = list(docs_dir.glob("*.docx")) + list(docs_dir.glob("*.pdf"))
            if doc_files:
                logger.info(f"Found {len(doc_files)} documents to upload")
                file_paths = [str(f) for f in doc_files]
                client.upload_files_to_vector_store(vector_store_id, file_paths)
            else:
                logger.warning(f"No documents found in {docs_dir}")
        else:
            logger.warning(f"Docs directory not found: {docs_dir}")
        
        # Attach vector store to assistant
        client.update_assistant(
            assistant_id,
            tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}}
        )
        
        logger.info(f"Assistant setup complete: {assistant_id}")
        return assistant_id
    
    def query(
        self,
        content: str,
        instructions: Optional[str] = None,
        temperature: float = 0.0
    ) -> str:
        """
        Query the assistant with automatic thread management.
        
        Args:
            content: The query content
            instructions: Optional runtime instructions
            temperature: Response randomness (0.0 = deterministic)
        
        Returns:
            Assistant's response text
        """
        assistant_id = self.get_or_create_assistant()
        
        # Create thread
        thread_id = client.create_thread()
        
        try:
            # Add message
            client.add_message(thread_id, content)
            
            # Run assistant
            client.run_assistant(
                thread_id=thread_id,
                assistant_id=assistant_id,
                instructions=instructions,
                temperature=temperature
            )
            
            # Get response
            messages = client.get_messages(thread_id, limit=1)
            if not messages:
                raise Exception("No response received from assistant")
            
            response_text = messages[0].content[0].text.value
            return response_text
        
        finally:
            # Always cleanup thread
            try:
                client.delete_thread(thread_id)
            except Exception as e:
                logger.warning(f"Failed to delete thread: {e}")
    
    def query_with_verification(
        self,
        content: str,
        instructions: Optional[str] = None
    ) -> str:
        """
        Query with two-pass verification (more expensive but accurate).
        
        Args:
            content: The query content
            instructions: Optional runtime instructions
        
        Returns:
            Verified assistant response
        """
        # First pass
        initial_response = self.query(content, instructions, temperature=0.0)
        
        # Verification pass
        verification_prompt = (
            f"Original input:\n{content}\n\n"
            f"Instructions given:\n{instructions}\n\n"
            f"Response provided:\n{initial_response}\n\n"
            "Review this response for:\n"
            "1. Adherence to instructions\n"
            "2. Factual accuracy vs input\n"
            "3. Consistency with Video Game Attributes\n\n"
            "If correct, return the original response unchanged. "
            "If errors found, return corrected version with minimal changes."
        )
        
        verified_response = self.query(verification_prompt, temperature=0.0)
        return verified_response
    
    def cleanup(self) -> None:
        """Delete assistant and associated resources."""
        if self.assistant_id:
            logger.info(f"Deleting assistant: {self.assistant_id}")
            client.delete_assistant(self.assistant_id)
            self.assistant_id = None

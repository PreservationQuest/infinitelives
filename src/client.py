"""
OpenAI API client with connection pooling, retry logic, and error handling.
"""
import time
import logging
from typing import Optional, List
from openai import OpenAI, RateLimitError, APITimeoutError, AuthenticationError
from functools import lru_cache

from .config import Config

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Singleton OpenAI client with retry logic and error handling."""
    
    _instance: Optional['OpenAIClient'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self) -> None:
        """Initialize the OpenAI client."""
        self.client = OpenAI(
            api_key=Config.OPENAI_API_KEY,
            organization=Config.OPENAI_ORG_ID,
            timeout=Config.REQUEST_TIMEOUT,
            max_retries=0  # We handle retries manually
        )
        logger.info("OpenAI client initialized")
    
    def _retry_with_backoff(self, func, *args, **kwargs):
        """Execute function with exponential backoff retry logic."""
        max_retries = Config.MAX_RETRIES
        base_delay = 2
        
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            
            except RateLimitError as e:
                if attempt == max_retries - 1:
                    raise
                delay = base_delay * (2 ** attempt)
                logger.warning(f"Rate limit hit. Retrying in {delay}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
            
            except APITimeoutError as e:
                if attempt == max_retries - 1:
                    raise
                delay = base_delay * (2 ** attempt)
                logger.warning(f"API timeout. Retrying in {delay}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
            
            except AuthenticationError as e:
                logger.error("Authentication failed. Check your API key.")
                raise
            
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                raise
    
    def create_assistant(
        self,
        instructions: str,
        model: str = None,
        tools: List[dict] = None,
        name: str = None
    ) -> str:
        """Create a new assistant."""
        model = model or Config.MODEL_NAME
        tools = tools or [{"type": "file_search"}]
        
        def _create():
            assistant = self.client.beta.assistants.create(
                name=name,
                instructions=instructions,
                model=model,
                tools=tools
            )
            logger.info(f"Created assistant: {assistant.id}")
            return assistant.id
        
        return self._retry_with_backoff(_create)
    
    def list_assistants(self) -> List:
        """List all assistants."""
        def _list():
            response = self.client.beta.assistants.list()
            return response.data
        
        return self._retry_with_backoff(_list)
    
    def get_assistant(self, assistant_id: str):
        """Get assistant by ID."""
        def _get():
            return self.client.beta.assistants.retrieve(assistant_id)
        
        return self._retry_with_backoff(_get)
    
    def update_assistant(self, assistant_id: str, **kwargs):
        """Update assistant configuration."""
        def _update():
            return self.client.beta.assistants.update(assistant_id, **kwargs)
        
        return self._retry_with_backoff(_update)
    
    def delete_assistant(self, assistant_id: str) -> None:
        """Delete an assistant."""
        def _delete():
            self.client.beta.assistants.delete(assistant_id)
            logger.info(f"Deleted assistant: {assistant_id}")
        
        return self._retry_with_backoff(_delete)
    
    def create_vector_store(self, name: str) -> str:
        """Create a vector store."""
        def _create():
            store = self.client.beta.vector_stores.create(name=name)
            logger.info(f"Created vector store: {store.id}")
            return store.id
        
        return self._retry_with_backoff(_create)
    
    def upload_files_to_vector_store(
        self,
        vector_store_id: str,
        file_paths: List[str]
    ) -> dict:
        """Upload files to vector store with polling."""
        def _upload():
            file_streams = [open(path, "rb") for path in file_paths]
            
            try:
                logger.info(f"Uploading {len(file_paths)} files to vector store...")
                file_batch = self.client.beta.vector_stores.file_batches.upload_and_poll(
                    vector_store_id=vector_store_id,
                    files=file_streams
                )
                
                # Poll until complete
                while file_batch.status not in ["completed", "failed"]:
                    logger.debug(f"Upload status: {file_batch.status}")
                    time.sleep(5)
                    file_batch = self.client.beta.vector_stores.file_batches.retrieve(
                        vector_store_id=vector_store_id,
                        batch_id=file_batch.id
                    )
                
                if file_batch.status == "failed":
                    raise Exception("File upload failed")
                
                logger.info(f"Upload completed: {file_batch.file_counts}")
                return file_batch.file_counts
            
            finally:
                for stream in file_streams:
                    stream.close()
        
        return self._retry_with_backoff(_upload)
    
    def create_thread(self) -> str:
        """Create a conversation thread."""
        def _create():
            thread = self.client.beta.threads.create()
            return thread.id
        
        return self._retry_with_backoff(_create)
    
    def add_message(self, thread_id: str, content: str, role: str = "user") -> None:
        """Add a message to thread."""
        def _add():
            self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role=role,
                content=content
            )
        
        return self._retry_with_backoff(_add)
    
    def run_assistant(
        self,
        thread_id: str,
        assistant_id: str,
        instructions: Optional[str] = None,
        temperature: float = 0.0
    ) -> str:
        """Run assistant and wait for completion."""
        def _run():
            # Create run
            run = self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id,
                instructions=instructions,
                temperature=temperature
            )
            
            # Poll for completion
            start_time = time.time()
            while run.status in ["queued", "in_progress"]:
                elapsed = time.time() - start_time
                
                if elapsed > Config.REQUEST_TIMEOUT:
                    raise TimeoutError(f"Run exceeded timeout of {Config.REQUEST_TIMEOUT}s")
                
                logger.debug(f"Run status: {run.status} ({elapsed:.1f}s elapsed)")
                time.sleep(2)
                
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
            
            if run.status == "failed":
                raise Exception(f"Run failed: {run.last_error}")
            
            return run.id
        
        return self._retry_with_backoff(_run)
    
    def get_messages(self, thread_id: str, limit: int = 1) -> List:
        """Get messages from thread."""
        def _get():
            messages = self.client.beta.threads.messages.list(
                thread_id=thread_id,
                limit=limit
            )
            return messages.data
        
        return self._retry_with_backoff(_get)
    
    def delete_thread(self, thread_id: str) -> None:
        """Delete a thread."""
        def _delete():
            self.client.beta.threads.delete(thread_id)
        
        return self._retry_with_backoff(_delete)


# Singleton instance
client = OpenAIClient()

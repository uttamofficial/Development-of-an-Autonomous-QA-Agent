"""
Configuration settings for the application.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""
    
    # Embedding model settings
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Vector DB settings
    vector_db_path: str = "data/vector_db"
    chroma_collection_name: str = "qa_agent_kb"
    
    # LLM settings (using dummy local model - no API key needed)
    llm_provider: str = "dummy-local"
    llm_model: str = "dummy-local"
    
    # Chunking settings
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # File paths
    uploaded_docs_path: str = "data/uploaded_docs"
    html_path: str = "data/html"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings (cached).
    
    Returns:
        Settings instance
    """
    return Settings()

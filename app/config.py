import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    app_name: str = "DocMind — AI Document Assistant"
    app_version: str = "1.0.0"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    debug: bool = True

    # RAG Settings matching original DocMind
    chunk_size: int = 700
    chunk_overlap: int = 100
    top_k: int = 5
    min_similarity: float = 0.0

    # Paths
    base_dir: Path = BASE_DIR
    data_dir: Path = BASE_DIR / "data"
    upload_dir: Path = BASE_DIR / "data" / "uploads"
    indices_dir: Path = BASE_DIR / "data" / "indices"

    # AI Model Providers
    embedding_model_name: str = "all-MiniLM-L6-v2"
    openai_api_key: str = ""
    openai_chat_model: str = "gpt-4o-mini"
    gemini_api_key: str = ""
    llm_provider: str = "auto"  # "auto", "openai", "gemini", or "local_grounded"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()

# Ensure directories exist
settings.data_dir.mkdir(parents=True, exist_ok=True)
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.indices_dir.mkdir(parents=True, exist_ok=True)

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Configuration
    app_name: str = "LLM Memory Agent"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # LLM Configuration
    llm_provider: str = "openai"  # "openai" or "anthropic"
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    llm_model: str = "gpt-4-turbo-preview"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 1000
    
    # Memory Configuration
    max_conversation_history: int = 10
    memory_decay_hours: int = 24
    enable_semantic_memory: bool = True
    enable_episodic_memory: bool = True
    
    # Redis Configuration (for production persistence)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    use_redis: bool = False
    
    # Security
    api_key_header: str = "X-API-Key"
    api_keys: list[str] = []  # Empty means no auth required
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

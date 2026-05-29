from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Medi_RAG"
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/medirag"
    redis_url: str = "redis://localhost:6379/0"
    llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    vllm_base_url: str = "http://localhost:8001"
    default_llm_model: str = "qwen2.5"
    default_embedding_model: str = "BAAI/bge-m3"
    workflow_state_ttl_seconds: int = 3600
    retrieval_chunk_size: int = 800
    retrieval_chunk_overlap: int = 120
    retrieval_top_k: int = 5
    retrieval_bm25_limit: int = 2000
    retrieval_query_rewrite: bool = False // 是否启用本地检索查询改写

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()

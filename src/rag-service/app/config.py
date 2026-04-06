# src/rag-service/app/config.py
# 역할: RAG Service 환경변수 관리
# 관련 챕터: Chapter 6

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_secret: str
    qdrant_url: str = "http://qdrant:6333"
    qdrant_collection: str = "company_docs"
    embedding_model: str = "snunlp/KR-SBERT-V40K-klueNLI-augSTS"  # 한국어 모델
    top_k_default: int = 5
    debug: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

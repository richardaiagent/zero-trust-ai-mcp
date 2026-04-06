# src/orchestrator/app/config.py
# 역할: Orchestrator 환경변수 관리
# 관련 챕터: Chapter 6

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    service_secret: str
    tool_server_url: str = "http://tool-service:8003"
    rag_service_url: str = "http://rag-service:8004"
    context_service_url: str = "http://context-service:8005"
    policy_engine_url: str = "http://policy-engine:8002"
    audit_service_url: str = "http://audit-service:8006"
    redis_url: str = "redis://redis:6379"
    debug: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

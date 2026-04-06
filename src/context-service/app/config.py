# src/context-service/app/config.py
# 역할: Context Service 환경변수 관리
# 관련 챕터: Chapter 2

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_secret: str
    redis_url: str = "redis://redis:6379"
    db_url: str = "postgresql://mcp_admin:password@postgres:5432/mcp_db"
    session_ttl_seconds: int = 3600   # 1시간
    max_history_turns: int = 10
    debug: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

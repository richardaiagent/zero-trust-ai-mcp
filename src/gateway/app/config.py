# src/gateway/app/config.py
# 역할: Gateway 환경변수 관리
# 관련 챕터: Chapter 6

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    orchestrator_url: str = "http://orchestrator:8001"
    redis_url: str = "redis://redis:6379"
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    service_secret: str
    rate_limit_per_minute: int = 20
    # ✅ Fix: monthly_token_quota 추가 (rate_limit.py 참조)
    monthly_token_quota: int = 1_000_000
    # ✅ Fix: openai_api_key 추가 (guard_llm.py 참조)
    openai_api_key: str = ""
    slack_webhook_url: str = ""
    debug: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

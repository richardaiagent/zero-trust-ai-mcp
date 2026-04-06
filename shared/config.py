# shared/config.py
# 역할: 전 서비스 공통 환경변수 베이스 설정
# 관련 챕터: Chapter 4

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str
    anthropic_api_key: str = ""
    service_secret: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    rate_limit_per_minute: int = 20
    monthly_token_quota: int = 10_000_000

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

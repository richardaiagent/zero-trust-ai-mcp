# src/policy-engine/app/config.py
# 역할: Policy Engine 환경변수 관리
# 관련 챕터: Chapter 9

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_secret: str
    opa_url: str = "http://opa:8181"
    debug: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

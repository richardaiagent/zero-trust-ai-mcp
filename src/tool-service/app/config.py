# src/tool-service/app/config.py
# 역할: Tool Service 환경변수 관리
# 관련 챕터: Chapter 6

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_secret: str
    db_url: str = ""     # db_query Tool에서 사용
    debug: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

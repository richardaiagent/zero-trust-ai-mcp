# src/audit-service/app/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    redis_url: str = "redis://redis:6379"
    service_secret: str
    debug: bool = False

    # 이상탐지 임계값
    anomaly_requests_per_hour_threshold: int = 100
    anomaly_policy_denied_ratio_threshold: float = 0.3
    anomaly_off_hours_start: int = 22  # 22시
    anomaly_off_hours_end: int = 6     # 06시

    slack_webhook_url: str = ""

    class Config:
        env_file = ".env"


settings = Settings()

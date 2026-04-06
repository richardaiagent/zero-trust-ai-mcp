# src/tool-service/app/middleware/service_auth.py
# 역할: 서비스 간 인증 — X-Service-Secret 헤더 검증
# 관련 챕터: Chapter 3

from fastapi import HTTPException, Header
from app.config import settings


async def verify_service_secret(x_service_secret: str = Header(...)) -> None:
    if x_service_secret != settings.service_secret:
        raise HTTPException(status_code=403, detail="Invalid service secret")

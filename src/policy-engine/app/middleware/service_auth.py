# src/policy-engine/app/middleware/service_auth.py
from fastapi import HTTPException, Header
from app.config import settings


async def verify_service_secret(x_service_secret: str = Header(...)) -> None:
    if x_service_secret != settings.service_secret:
        raise HTTPException(status_code=403, detail="Invalid service secret")

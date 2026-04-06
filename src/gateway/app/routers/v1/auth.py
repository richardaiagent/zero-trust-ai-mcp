# src/gateway/app/routers/v1/auth.py
# 역할: JWT 발급 / 갱신 / 로그아웃
# 관련 챕터: Chapter 9

import uuid
import logging
from datetime import datetime, timedelta

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Request
from jose import jwt
from pydantic import BaseModel

from app.config import settings
from app.middleware.auth import verify_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


class TokenRequest(BaseModel):
    api_key: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# 개발용 API Key → user_id / role 매핑 (운영에서는 DB 조회)
_DEV_API_KEYS: dict[str, dict] = {
    "dev-api-key-1234": {"user_id": "user-001", "role": "analyst"},
    "dev-admin-key":    {"user_id": "user-002", "role": "admin"},
}


def _create_access_token(user_id: str, role: str) -> str:
    payload = {
        "sub":  user_id,
        "role": role,
        "exp":  datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes),
        "jti":  str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


@router.post("/token", response_model=TokenResponse)
async def issue_token(body: TokenRequest, request: Request) -> TokenResponse:
    user_info = _DEV_API_KEYS.get(body.api_key)
    if not user_info:
        raise HTTPException(status_code=401, detail="Invalid API key")

    access_token  = _create_access_token(user_info["user_id"], user_info["role"])
    refresh_token = str(uuid.uuid4())

    redis: aioredis.Redis = request.app.state.redis
    await redis.setex(f"refresh:{refresh_token}", 60 * 60 * 24 * 7, user_info["user_id"])

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(refresh_token: str, request: Request) -> TokenResponse:
    redis: aioredis.Redis = request.app.state.redis
    user_id = await redis.get(f"refresh:{refresh_token}")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    # Rotation: 기존 폐기, 새 토큰 발급
    await redis.delete(f"refresh:{refresh_token}")
    new_refresh = str(uuid.uuid4())
    await redis.setex(f"refresh:{new_refresh}", 60 * 60 * 24 * 7, user_id)

    # 역할 재조회 (개발용: 고정)
    role = "analyst"
    new_access = _create_access_token(user_id, role)

    return TokenResponse(access_token=new_access, refresh_token=new_refresh)


@router.post("/logout")
async def logout(token: dict = Depends(verify_token), request: Request = None) -> dict:
    redis: aioredis.Redis = request.app.state.redis
    jti = token.get("jti")
    exp = token.get("exp")
    if jti and exp:
        remaining = int(exp - datetime.utcnow().timestamp())
        if remaining > 0:
            await redis.setex(f"blacklist:jti:{jti}", remaining, "1")
    return {"message": "로그아웃 완료"}

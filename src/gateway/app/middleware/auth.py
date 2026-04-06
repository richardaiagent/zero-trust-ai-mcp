# src/gateway/app/middleware/auth.py
# 역할: JWT 토큰 검증 + JTI 블랙리스트 확인
# 관련 챕터: Chapter 6, 9

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import redis.asyncio as aioredis

from app.config import settings

bearer_scheme = HTTPBearer()


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    request: Request = None,
) -> dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        jti: str = payload.get("jti")

        if not user_id or not role:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        # JTI 블랙리스트 확인 (로그아웃 처리된 토큰 차단)
        if request and jti:
            redis: aioredis.Redis = request.app.state.redis
            if await redis.exists(f"blacklist:jti:{jti}"):
                raise HTTPException(status_code=401, detail="Token has been revoked")

        return {"sub": user_id, "role": role, "jti": jti}

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

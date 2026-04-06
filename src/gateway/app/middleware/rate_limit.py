# src/gateway/app/middleware/rate_limit.py
# 역할: Sliding Window Rate Limiter (Redis Sorted Set 기반)
# 관련 챕터: Chapter 2, 6

import time
from fastapi import Request, HTTPException
import redis.asyncio as aioredis

from app.config import settings


class RateLimiter:

    async def check(self, request: Request, user_id: str) -> None:
        redis: aioredis.Redis = request.app.state.redis
        key = f"rate:{user_id}"
        now = time.time()
        window = 60  # 1분 슬라이딩 윈도우

        pipe = redis.pipeline()
        pipe.zremrangebyscore(key, 0, now - window)   # 윈도우 밖 항목 제거
        pipe.zadd(key, {str(now): now})               # 현재 요청 추가
        pipe.zcard(key)                               # 현재 윈도우 요청 수
        pipe.expire(key, window)
        results = await pipe.execute()

        count = results[2]
        if count > settings.rate_limit_per_minute:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: max {settings.rate_limit_per_minute} req/min",
            )

    async def check_monthly_quota(self, redis: aioredis.Redis, user_id: str, tokens_used: int) -> None:
        key = f"quota:{user_id}:{time.strftime('%Y-%m')}"
        total = await redis.incrby(key, tokens_used)
        await redis.expire(key, 60 * 60 * 24 * 35)   # 35일 TTL

        if total > settings.monthly_token_quota:
            raise HTTPException(status_code=429, detail="Monthly token quota exceeded.")


def get_rate_limiter() -> RateLimiter:
    return RateLimiter()

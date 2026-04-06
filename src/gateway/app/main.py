# src/gateway/app/main.py
# 역할: MCP Gateway — 외부 요청 단일 진입점
# 관련 챕터: Chapter 6

from contextlib import asynccontextmanager
import redis.asyncio as aioredis
from fastapi import FastAPI
from prometheus_client import make_asgi_app

from app.config import settings
from app.routers.v1 import chat, auth
from shared.logging import setup_logging
from shared.middleware.metrics_middleware import MetricsMiddleware

setup_logging("gateway", level="DEBUG" if settings.debug else "INFO")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Redis 연결 (Rate Limit, JWT 블랙리스트, Refresh Token 저장)
    app.state.redis = await aioredis.from_url(settings.redis_url, decode_responses=True)
    yield
    await app.state.redis.close()


app = FastAPI(
    title="MCP Gateway",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
)

app.add_middleware(MetricsMiddleware, service_name="gateway")

app.include_router(chat.router, prefix="/v1")
app.include_router(auth.router, prefix="/v1")

# Prometheus 메트릭 엔드포인트
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/healthz")
async def health():
    return {"status": "ok", "version": "1.0.0"}

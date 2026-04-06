# src/audit-service/app/main.py
# 역할: MCP Audit Service — 감사 로그 수집 & 이상탐지
# 관련 챕터: Chapter 4, 10, 13

import asyncio
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from prometheus_client import make_asgi_app

from app.routers.audit import router as audit_router
from app.subscriber import run_subscriber
from app.config import settings
from shared.logging import setup_logging

setup_logging("audit-service", level="DEBUG" if settings.debug else "INFO")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = await aioredis.from_url(settings.redis_url, decode_responses=True)
    # Redis Pub/Sub 구독자를 백그라운드 태스크로 실행
    task = asyncio.create_task(run_subscriber(app.state.redis))
    yield
    task.cancel()
    await app.state.redis.close()


app = FastAPI(title="MCP Audit Service", version="1.0.0", lifespan=lifespan, docs_url=None)

app.include_router(audit_router)
app.mount("/metrics", make_asgi_app())


@app.get("/healthz")
async def health():
    return {"status": "ok"}

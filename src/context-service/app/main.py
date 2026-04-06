# src/context-service/app/main.py
# 역할: MCP Context Service — 세션 히스토리 관리
# 관련 챕터: Chapter 2

from contextlib import asynccontextmanager
import redis.asyncio as aioredis
from fastapi import FastAPI

from app.routers.context import router as context_router
from app.config import settings
from shared.logging import setup_logging

setup_logging("context-service", level="DEBUG" if settings.debug else "INFO")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = await aioredis.from_url(settings.redis_url, decode_responses=True)
    yield
    await app.state.redis.close()


app = FastAPI(title="MCP Context Service", version="1.0.0", lifespan=lifespan, docs_url=None)

app.include_router(context_router)


@app.get("/healthz")
async def health():
    return {"status": "ok"}

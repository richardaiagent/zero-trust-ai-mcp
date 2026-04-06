# src/policy-engine/app/main.py
# 역할: MCP Policy Engine — OPA 연동 Zero Trust 정책 판단 서비스
# 관련 챕터: Chapter 9

from fastapi import FastAPI
from app.routers.policy import router
from app.config import settings
from shared.logging import setup_logging

setup_logging("policy-engine", level="DEBUG" if settings.debug else "INFO")

app = FastAPI(title="MCP Policy Engine", version="1.0.0", docs_url=None)

app.include_router(router, prefix="/policy")


@app.get("/healthz")
async def health():
    return {"status": "ok"}

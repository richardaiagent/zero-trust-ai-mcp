# src/tool-service/app/main.py
# 역할: MCP Tool Server — 외부 도구 실행 서비스
# 관련 챕터: Chapter 6

from fastapi import FastAPI
from app.routers.tools import router as tools_router
from app.config import settings
from shared.logging import setup_logging

setup_logging("tool-service", level="DEBUG" if settings.debug else "INFO")

app = FastAPI(title="MCP Tool Server", version="1.0.0", docs_url=None)

app.include_router(tools_router)


@app.get("/healthz")
async def health():
    return {"status": "ok"}

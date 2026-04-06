# src/orchestrator/app/main.py
# 역할: MCP Orchestrator — 핵심 오케스트레이션 서비스 (내부망 전용)
# 관련 챕터: Chapter 6

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from app.routers.internal import router as internal_router
from app.config import settings
from shared.logging import setup_logging
from shared.middleware.metrics_middleware import MetricsMiddleware

setup_logging("orchestrator", level="DEBUG" if settings.debug else "INFO")

app = FastAPI(title="MCP Orchestrator", version="1.0.0", docs_url=None)

app.add_middleware(MetricsMiddleware, service_name="orchestrator")

app.include_router(internal_router)

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/healthz")
async def health():
    return {"status": "ok", "version": "1.0.0"}

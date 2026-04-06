# src/rag-service/app/main.py
# 역할: MCP RAG Service — 벡터 유사도 검색 서비스
# 관련 챕터: Chapter 6

from fastapi import FastAPI
from app.routers.rag import router as rag_router
from app.config import settings
from shared.logging import setup_logging

setup_logging("rag-service", level="DEBUG" if settings.debug else "INFO")

app = FastAPI(title="MCP RAG Service", version="1.0.0", docs_url=None)

app.include_router(rag_router)


@app.get("/healthz")
async def health():
    return {"status": "ok"}

# src/orchestrator/app/clients/rag_client.py
# 역할: RAG Service HTTP 클라이언트
# 관련 챕터: Chapter 6

import httpx
from app.config import settings


class RagClient:

    async def search(self, query: str, top_k: int = 5) -> dict:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{settings.rag_service_url}/rag/search",
                json={"query": query, "top_k": top_k},
                headers={"X-Service-Secret": settings.service_secret},
            )
            resp.raise_for_status()
            return resp.json()

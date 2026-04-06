# src/tool-service/app/executor.py
# 역할: Tool 실행 엔진 — Registry 기반, 확장 가능한 구조
# 관련 챕터: Chapter 6

import logging
import asyncpg
import httpx

from app.registry import TOOL_REGISTRY
from app.config import settings

logger = logging.getLogger(__name__)


class ToolExecutor:

    async def run(self, tool_name: str, parameters: dict) -> dict:
        if tool_name not in TOOL_REGISTRY:
            raise ValueError(f"Tool '{tool_name}' not registered")

        handler = getattr(self, f"_exec_{tool_name}", None)
        if not handler:
            raise NotImplementedError(f"Executor for '{tool_name}' not implemented")

        return await handler(parameters)

    async def _exec_db_query(self, params: dict) -> dict:
        """Sales/Inventory DB 조회 Tool"""
        query   = params["query"]
        db_name = params.get("db_name", "sales")

        # ⚠️ 운영에서는 ORM + 파라미터 바인딩 필수. 여기선 예시용 단순 쿼리.
        conn = await asyncpg.connect(dsn=settings.db_url)
        try:
            rows = await conn.fetch(query)
            return {"rows": [dict(r) for r in rows], "count": len(rows), "db_name": db_name}
        finally:
            await conn.close()

    async def _exec_get_weather(self, params: dict) -> dict:
        """외부 날씨 API 호출 Tool"""
        city = params["city"]
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"https://wttr.in/{city}?format=j1")
            data = resp.json()
            current = data["current_condition"][0]
            return {
                "city":   city,
                "temp_c": current["temp_C"],
                "desc":   current["weatherDesc"][0]["value"],
            }

    async def _exec_send_email(self, params: dict) -> dict:
        """이메일 발송 Tool (개발용 — 실제 발송 미구현)"""
        logger.info("email send | to=%s subject=%s", params.get("to"), params.get("subject"))
        return {"status": "sent", "to": params["to"]}

    async def _exec_search_docs(self, params: dict) -> dict:
        """사내 문서 검색 Tool (RAG Service 호출)"""
        keyword = params["keyword"]
        # 실제로는 RAG Service로 위임. 여기선 빈 결과 반환.
        return {"keyword": keyword, "results": []}

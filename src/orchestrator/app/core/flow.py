# src/orchestrator/app/core/flow.py
# 역할: MCP 핵심 오케스트레이션 — 의도 분석 → Tool/RAG → LLM → 컨텍스트 저장
# 흐름: Context → Tool 목록 → Intent 분석 → Policy → Tool/LLM → 저장
# 관련 챕터: Chapter 6

import json
import logging
from openai import AsyncOpenAI

from app.clients.tool_client import ToolClient
from app.clients.context_client import ContextClient
from app.clients.policy_client import PolicyClient
from app.clients.rag_client import RagClient
from app.core.router import route_to_model
from app.config import settings
from shared.metrics import LLM_CALL_COUNT, LLM_LATENCY, LLM_TOKENS

logger = logging.getLogger(__name__)

_openai = AsyncOpenAI(api_key=settings.openai_api_key)
_tool   = ToolClient()
_ctx    = ContextClient()
_policy = PolicyClient()
_rag    = RagClient()


class OrchestrationFlow:

    async def run(
        self,
        session_id: str,
        user_id: str,
        role: str,
        message: str,
        request_id: str,
    ) -> dict:

        # 1. 컨텍스트 로드
        context = await _ctx.get(session_id, user_id)
        history = context.get("conversation_history", [])

        # 2. 역할 기반 Tool 목록 조회
        available_tools = await _tool.list(role=role)

        # 3. 의도 분석 (경량 모델)
        intent = await self._analyze_intent(message, history, available_tools)
        logger.info("intent | session=%s tool=%s", session_id, intent.get("tool_name"))

        result_message = ""
        sources: list = []
        model_used = ""

        if intent.get("tool_name"):
            # ── Tool 실행 경로 ──────────────────────────────
            tool_name = intent["tool_name"]
            params    = intent.get("parameters", {})

            # Policy Engine 확인 (Zero Trust: 실행 전 매번 검증)
            allowed = await _policy.check(
                user_id=user_id, role=role,
                resource=f"tool:{tool_name}", action="execute",
                context={"parameters": params},
            )
            if not allowed:
                return {"message": "해당 작업에 대한 권한이 없습니다.", "sources": [], "model_used": "none"}

            tool_result = await _tool.execute(tool_name, params, user_id, role)

            # Tool 결과를 LLM으로 종합
            model = route_to_model(requires_reasoning=True, history_len=len(history))
            response = await _openai.chat.completions.create(
                model=model,
                messages=[
                    *history,
                    {"role": "user",   "content": message},
                    {"role": "system", "content": f"도구 실행 결과:\n{json.dumps(tool_result, ensure_ascii=False)}\n\n위 결과를 바탕으로 사용자에게 명확하게 답해줘."},
                ],
            )
            result_message = response.choices[0].message.content
            model_used     = model
            self._record_llm_metrics(model, response)

        else:
            # ── 직접 LLM 응답 경로 ──────────────────────────
            model = route_to_model(history_len=len(history))
            response = await _openai.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "당신은 기업용 AI 어시스턴트입니다. 정확하고 간결하게 답변하세요."},
                    *history,
                    {"role": "user", "content": message},
                ],
            )
            result_message = response.choices[0].message.content
            model_used     = model
            self._record_llm_metrics(model, response)

        # 4. 컨텍스트 저장
        await _ctx.save_turn(session_id, message, result_message)

        return {"message": result_message, "sources": sources, "model_used": model_used}

    async def _analyze_intent(self, message: str, history: list, tools: list) -> dict:
        """경량 모델로 의도 분석 — Tool 필요 여부와 파라미터 결정."""
        tool_specs = json.dumps(tools, ensure_ascii=False)
        response = await _openai.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"사용 가능한 도구 목록:\n{tool_specs}\n\n"
                        "사용자 메시지를 분석해서 JSON으로 응답하라.\n"
                        "도구가 필요하면: {\"tool_name\": \"도구명\", \"parameters\": {...}}\n"
                        "불필요하면: {\"tool_name\": null, \"parameters\": {}}"
                    ),
                },
                {"role": "user", "content": message},
            ],
        )
        return json.loads(response.choices[0].message.content)

    @staticmethod
    def _record_llm_metrics(model: str, response) -> None:
        LLM_CALL_COUNT.labels(model=model, provider="openai", is_fallback="false").inc()
        if response.usage:
            LLM_TOKENS.labels(model=model, type="input").inc(response.usage.prompt_tokens)
            LLM_TOKENS.labels(model=model, type="output").inc(response.usage.completion_tokens)

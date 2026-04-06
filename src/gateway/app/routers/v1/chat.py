# src/gateway/app/routers/v1/chat.py
# 역할: POST /v1/chat — 인증+Rate Limit+DLP+Guard LLM 후 Orchestrator 위임
# 관련 챕터: Chapter 6, 10

import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from fastapi.responses import StreamingResponse

from app.middleware.auth import verify_token
from app.middleware.rate_limit import RateLimiter, get_rate_limiter
from app.clients.orchestrator import OrchestratorClient
from app.schemas.chat import ChatRequest, ChatResponse, Source
from app.security.dlp_engine import DLPEngine
from app.security.guard_llm import GuardLLM, ThreatLevel
from app.config import settings
from shared.security.alert import SecurityAlertService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

_orchestrator = OrchestratorClient()
_dlp          = DLPEngine()
_guard        = GuardLLM()  # ✅ Fix: 인자 제거 (내부에서 settings 참조)
_alert        = SecurityAlertService(slack_webhook_url=settings.slack_webhook_url)


@router.post("", response_model=ChatResponse)
async def chat(
    request: Request,
    body: ChatRequest,
    x_request_id: str = Header(default=None),
    token: dict = Depends(verify_token),
    limiter: RateLimiter = Depends(get_rate_limiter),
) -> ChatResponse:
    req_id  = x_request_id or str(uuid.uuid4())
    user_id = token["sub"]

    # 1. Rate Limit 확인
    await limiter.check(request, user_id=user_id)

    # 2. Guard LLM — 프롬프트 인젝션 / 탈옥 탐지
    guard_result = await _guard.evaluate(body.message)
    if guard_result["level"] == ThreatLevel.ATTACK:
        await _alert.send(level="HIGH", event="GUARD_LLM_ATTACK", detail=guard_result, user_id=user_id)
        raise HTTPException(status_code=400, detail="보안 정책에 위반된 요청입니다.")
    if guard_result["level"] == ThreatLevel.SUSPECT:
        await _alert.send(level="MEDIUM", event="GUARD_LLM_SUSPECT", detail=guard_result, user_id=user_id)

    # 3. DLP 입력 검사
    input_scan = _dlp.scan(body.message)
    if input_scan.is_blocked:
        await _alert.send(level="HIGH", event="DLP_INPUT_BLOCK", detail=input_scan.detections, user_id=user_id)
        raise HTTPException(status_code=400, detail="요청에 허용되지 않는 민감 정보가 포함되어 있습니다.")

    # 4. 스트리밍 처리
    if body.stream:
        return StreamingResponse(
            _orchestrator.stream(body.session_id, body.message, user_id, token["role"], req_id),
            media_type="text/event-stream",
        )

    # 5. Orchestrator 동기 호출
    try:
        result = await _orchestrator.invoke(
            session_id=body.session_id,
            message=body.message,
            user_id=user_id,
            role=token["role"],
            request_id=req_id,
        )
    except Exception as e:
        logger.error("orchestrator error | req_id=%s err=%s", req_id, e)
        raise HTTPException(status_code=502, detail="AI 서비스 일시적 오류")

    # 6. DLP 출력 검사 + 마스킹
    output_scan = _dlp.scan(result["message"])
    if output_scan.detections:
        await _alert.send(
            level=str(output_scan.max_level),
            event="DLP_OUTPUT_DETECTED",
            detail=output_scan.detections,
            user_id=user_id,
        )

    sources = [Source(**s) for s in result.get("sources", [])]

    return ChatResponse(
        session_id=body.session_id,
        message=output_scan.masked,
        sources=sources,
        model_used=result.get("model_used", "unknown"),
        request_id=req_id,
    )

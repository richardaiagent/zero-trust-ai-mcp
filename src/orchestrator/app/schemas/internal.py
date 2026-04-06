# src/orchestrator/app/schemas/internal.py
# 역할: Orchestrator 내부 API 스키마
# 관련 챕터: Chapter 3

from pydantic import BaseModel


class InvokeRequest(BaseModel):
    session_id: str
    user_id: str
    role: str
    message: str
    request_id: str


class InvokeResponse(BaseModel):
    session_id: str
    message: str
    sources: list = []
    model_used: str
    request_id: str

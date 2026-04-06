# src/context-service/app/schemas/context.py
# 역할: Context 요청/응답 스키마
# 관련 챕터: Chapter 2

from pydantic import BaseModel


class ContextResponse(BaseModel):
    session_id: str
    user_id: str
    conversation_history: list[dict]


class TurnRequest(BaseModel):
    user: str
    assistant: str

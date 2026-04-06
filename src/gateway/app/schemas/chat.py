# src/gateway/app/schemas/chat.py
# 역할: Gateway 채팅 요청/응답 Pydantic 스키마
# 관련 챕터: Chapter 6

from typing import Optional, List
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="대화 세션 ID")
    message: str = Field(..., max_length=4000, description="사용자 메시지")
    stream: bool = Field(default=False)


class Source(BaseModel):
    title: str
    url: Optional[str] = None
    content: str


class ChatResponse(BaseModel):
    session_id: str
    message: str
    sources: List[Source] = []
    model_used: str
    request_id: str

# src/policy-engine/app/schemas/policy.py
# 역할: Policy 요청/응답 스키마
# 관련 챕터: Chapter 9

from pydantic import BaseModel


class PolicyCheckRequest(BaseModel):
    user_id: str
    role: str
    resource: str       # 예: "tool:db_query"
    action: str         # 예: "execute"
    context: dict = {}  # 추가 컨텍스트 (파라미터, 시간대 등)


class PolicyCheckResponse(BaseModel):
    allowed: bool
    reason: str

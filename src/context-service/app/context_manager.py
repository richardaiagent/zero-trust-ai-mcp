# src/context-service/app/context_manager.py
# 역할: 단기(Redis) + 장기(PostgreSQL) 컨텍스트 관리
# 관련 챕터: Chapter 2

import json
import logging
import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)


class ContextManager:

    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client

    async def build_context(self, session_id: str, user_id: str) -> dict:
        """단기 히스토리(Redis) + 사용자 프로파일 조합"""
        # 단기: 최근 max_history_turns 턴의 대화 히스토리
        raw_history = await self.redis.lrange(
            f"session:{session_id}:history",
            -settings.max_history_turns * 2,  # user + assistant 쌍
            -1,
        )

        # Redis에서 꺼낸 문자열을 OpenAI 메시지 포맷으로 변환
        conversation_history = []
        for i in range(0, len(raw_history), 2):
            if i + 1 < len(raw_history):
                conversation_history.append({"role": "user",      "content": raw_history[i]})
                conversation_history.append({"role": "assistant", "content": raw_history[i + 1]})

        return {
            "conversation_history": conversation_history,
            "session_id": session_id,
            "user_id": user_id,
        }

    async def save_turn(self, session_id: str, user_msg: str, ai_msg: str) -> None:
        """대화 한 턴을 Redis에 저장 (Sliding Window)"""
        key = f"session:{session_id}:history"
        pipe = self.redis.pipeline()
        pipe.rpush(key, user_msg, ai_msg)
        pipe.expire(key, settings.session_ttl_seconds)

        # max 턴 초과 시 오래된 것 제거 (LTRIM)
        max_entries = settings.max_history_turns * 2
        pipe.ltrim(key, -max_entries, -1)
        await pipe.execute()

    async def delete_session(self, session_id: str) -> None:
        await self.redis.delete(f"session:{session_id}:history")

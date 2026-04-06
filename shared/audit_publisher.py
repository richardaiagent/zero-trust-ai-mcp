# shared/audit_publisher.py
# 역할: Redis Pub/Sub 기반 감사 이벤트 발행 (비동기 fire-and-forget)
# 관련 챕터: Chapter 4

import json
import logging
import redis.asyncio as aioredis
from datetime import datetime

logger = logging.getLogger(__name__)


class AuditPublisher:
    CHANNEL = "mcp:audit:events"

    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client

    async def publish(self, event_type: str, payload: dict, trace_id: str) -> None:
        event = {
            "event_type": event_type,
            "payload": payload,
            "trace_id": trace_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        try:
            await self.redis.publish(self.CHANNEL, json.dumps(event, ensure_ascii=False))
        except Exception as e:
            # 발행 실패가 메인 흐름을 막으면 안 됨
            logger.error("audit publish failed: %s", e)

# src/audit-service/app/schemas/audit.py
# Chapter 2: 감사 이벤트 스키마

from enum import Enum
from datetime import datetime
from pydantic import BaseModel


class AuditEventType(str, Enum):
    request_received = "request_received"
    policy_decision  = "policy_decision"
    tool_executed    = "tool_executed"
    llm_called       = "llm_called"
    response_sent    = "response_sent"
    anomaly_detected = "anomaly_detected"
    security_alert   = "security_alert"


class AuditEvent(BaseModel):
    event_type:  AuditEventType
    session_id:  str
    user_id:     str
    trace_id:    str = ""
    timestamp:   datetime = None
    detail:      dict = {}

    def model_post_init(self, __context):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

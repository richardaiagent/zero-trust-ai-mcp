# shared/logging.py
# 역할: 구조화된 JSON 로깅 — Loki/ELK 수집에 최적화
# 관련 챕터: Chapter 13

import logging
import json
from datetime import datetime


class JSONFormatter(logging.Formatter):

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level":     record.levelname,
            "service":   getattr(record, "service", "unknown"),
            "message":   record.getMessage(),
            "logger":    record.name,
            "trace_id":  getattr(record, "trace_id", None),
            "user_id":   getattr(record, "user_id", None),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj, ensure_ascii=False)


def setup_logging(service_name: str, level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)

    # 모든 로그에 service 필드 자동 추가
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.service = service_name
        return record

    logging.setLogRecordFactory(record_factory)

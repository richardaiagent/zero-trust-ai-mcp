# src/gateway/app/security/dlp_engine.py
# 역할: DLP 입/출력 민감 정보 탐지 및 마스킹
# 관련 챕터: Chapter 10

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class DLPLevel(str, Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"


@dataclass
class DLPPattern:
    name: str
    pattern: re.Pattern
    level: DLPLevel


# 탐지 패턴 정의
DLP_PATTERNS: list[DLPPattern] = [
    DLPPattern("주민등록번호",  re.compile(r"\b\d{6}[-\s]?\d{7}\b"),                                    DLPLevel.HIGH),
    DLPPattern("신용카드번호",  re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),                             DLPLevel.HIGH),
    DLPPattern("계좌번호",      re.compile(r"\b\d{3,6}[-\s]?\d{6,14}[-\s]?\d{2,3}\b"),                 DLPLevel.MEDIUM),
    DLPPattern("전화번호",      re.compile(r"\b0\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4}\b"),                   DLPLevel.LOW),
    DLPPattern("이메일",        re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),   DLPLevel.LOW),
    DLPPattern("AWS_ACCESS_KEY",re.compile(r"\bAKIA[0-9A-Z]{16}\b"),                                    DLPLevel.HIGH),
    DLPPattern("비밀번호_패턴", re.compile(r"(?i)(?:password|passwd|pw)\s*[=:]\s*\S+"),                 DLPLevel.HIGH),
]


@dataclass
class DLPScanResult:
    original: str
    masked: str
    detections: list[dict] = field(default_factory=list)
    max_level: Optional[DLPLevel] = None
    is_blocked: bool = False


class DLPEngine:

    def scan(self, text: str) -> DLPScanResult:
        masked = text
        detections: list[dict] = []
        max_level: Optional[DLPLevel] = None

        for dp in DLP_PATTERNS:
            matches = list(dp.pattern.finditer(masked))
            if not matches:
                continue

            for match in reversed(matches):   # 뒤에서부터 치환해야 인덱스가 밀리지 않음
                val = match.group()
                mask_len = max(4, len(val) - 4)
                masked_val = val[:2] + ("*" * mask_len) + val[-2:]
                masked = masked[:match.start()] + masked_val + masked[match.end():]

            detections.append({"type": dp.name, "count": len(matches), "level": dp.level})

            if max_level is None or self._rank(dp.level) > self._rank(max_level):
                max_level = dp.level

        return DLPScanResult(
            original=text,
            masked=masked,
            detections=detections,
            max_level=max_level,
            is_blocked=(max_level == DLPLevel.HIGH),
        )

    @staticmethod
    def _rank(level: DLPLevel) -> int:
        return {DLPLevel.LOW: 1, DLPLevel.MEDIUM: 2, DLPLevel.HIGH: 3}[level]

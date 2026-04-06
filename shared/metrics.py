# shared/metrics.py
# 역할: Prometheus 메트릭 정의 — 전 서비스 공유
# 관련 챕터: Chapter 13

from prometheus_client import Counter, Histogram, Gauge

# ── 요청 메트릭 ────────────────────────────────
REQUEST_COUNT = Counter(
    "mcp_requests_total",
    "총 요청 수",
    ["service", "endpoint", "status_code"],
)
REQUEST_LATENCY = Histogram(
    "mcp_request_duration_seconds",
    "요청 응답 시간 (초)",
    ["service", "endpoint"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# ── LLM 메트릭 ─────────────────────────────────
LLM_CALL_COUNT = Counter(
    "mcp_llm_calls_total",
    "LLM 호출 횟수",
    ["model", "provider", "is_fallback"],
)
LLM_LATENCY = Histogram(
    "mcp_llm_latency_seconds",
    "LLM 응답 지연 시간",
    ["model"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
)
LLM_TOKENS = Counter(
    "mcp_llm_tokens_total",
    "LLM 토큰 사용량",
    ["model", "type"],  # type: input | output
)
LLM_COST = Counter(
    "mcp_llm_cost_usd_total",
    "LLM 누적 비용 (USD)",
    ["model"],
)

# ── 보안 메트릭 ────────────────────────────────
DLP_DETECTIONS = Counter(
    "mcp_dlp_detections_total",
    "DLP 탐지 건수",
    ["level", "type"],
)
GUARD_ATTACKS = Counter(
    "mcp_guard_llm_attacks_total",
    "Guard LLM 공격 판정 건수",
    ["threat_type"],
)

# ── 캐시 메트릭 ────────────────────────────────
CACHE_HITS = Counter("mcp_cache_hits_total", "시맨틱 캐시 히트", ["model"])
CACHE_MISSES = Counter("mcp_cache_misses_total", "시맨틱 캐시 미스", ["model"])

# ── Circuit Breaker ─────────────────────────────
CIRCUIT_STATE = Gauge(
    "mcp_circuit_breaker_state",
    "Circuit Breaker 상태 (0=closed, 1=half_open, 2=open)",
    ["provider"],
)

# ── Tool 메트릭 ────────────────────────────────
TOOL_EXEC_COUNT = Counter(
    "mcp_tool_executions_total",
    "Tool별 실행 횟수",
    ["tool_name"],
)
TOOL_ERROR_COUNT = Counter(
    "mcp_tool_errors_total",
    "Tool별 에러 수",
    ["tool_name"],
)

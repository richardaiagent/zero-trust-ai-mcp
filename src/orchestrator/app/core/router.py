# src/orchestrator/app/core/router.py
# 역할: 복잡도 점수 기반 Multi-model Routing
# 관련 챕터: Chapter 2, 6

MODEL_MAP = {
    "fast":     "gpt-4o-mini",       # 빠르고 저렴 (요약, 분류, 간단 QA)
    "balanced": "gpt-4o",            # 균형 (일반 업무 보조)
    "power":    "claude-opus-4-6",   # 강력 (복잡한 추론, 코드 생성)
}


def route_to_model(
    requires_reasoning: bool = False,
    code_gen: bool = False,
    history_len: int = 0,
) -> str:
    """복잡도 점수로 모델 티어 결정. LLM이 아닌 규칙 기반."""
    score = 0
    if requires_reasoning:
        score += 3
    if code_gen:
        score += 2
    if history_len > 5:
        score += 1

    if score >= 4:
        return MODEL_MAP["power"]
    elif score >= 2:
        return MODEL_MAP["balanced"]
    return MODEL_MAP["fast"]

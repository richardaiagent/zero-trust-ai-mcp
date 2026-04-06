# src/tool-service/app/registry.py
# 역할: Tool 중앙 레지스트리 — 등록 + 역할 기반 필터링
# 관련 챕터: Chapter 2, 6

TOOL_REGISTRY: dict[str, dict] = {
    "db_query": {
        "name":        "db_query",
        "description": "sales DB에서 데이터를 조회한다",
        "parameters": {
            "type": "object",
            "properties": {
                "query":   {"type": "string", "description": "실행할 SQL 쿼리"},
                "db_name": {"type": "string", "enum": ["sales", "hr", "inventory"]},
            },
            "required": ["query", "db_name"],
        },
        "required_role": ["analyst", "admin"],
        "timeout_sec":   10,
    },
    "send_email": {
        "name":        "send_email",
        "description": "이메일을 발송한다",
        "parameters": {
            "type": "object",
            "properties": {
                "to":      {"type": "string"},
                "subject": {"type": "string"},
                "body":    {"type": "string"},
            },
            "required": ["to", "subject", "body"],
        },
        "required_role": ["admin"],
        "timeout_sec":   5,
    },
    "get_weather": {
        "name":        "get_weather",
        "description": "도시의 현재 날씨를 조회한다",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "도시 이름 (영문)"},
            },
            "required": ["city"],
        },
        "required_role": ["viewer", "analyst", "admin"],
        "timeout_sec":   5,
    },
    "search_docs": {
        "name":        "search_docs",
        "description": "사내 문서를 키워드로 검색한다",
        "parameters": {
            "type": "object",
            "properties": {
                "keyword": {"type": "string"},
            },
            "required": ["keyword"],
        },
        "required_role": ["viewer", "analyst", "admin"],
        "timeout_sec":   5,
    },
}


def get_tools_for_role(role: str) -> list[dict]:
    """사용자 역할에 맞는 Tool만 필터링해서 반환. LLM은 이 목록만 인식한다."""
    return [
        {k: v for k, v in tool.items() if k != "required_role"}
        for tool in TOOL_REGISTRY.values()
        if role in tool["required_role"]
    ]

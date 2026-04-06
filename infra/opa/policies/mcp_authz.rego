# infra/opa/policies/mcp_authz.rego
# Chapter 9: MCP 플랫폼 ABAC 정책 (OPA Rego)
#
# 평가 URL: POST http://opa:8181/v1/data/mcp/authz/allow
# 입력 형식:
#   {
#     "input": {
#       "user_id":  "user-123",
#       "role":     "analyst",
#       "resource": "db_query",
#       "action":   "execute",
#       "context":  { "hour": 14, "department": "engineering" }
#     }
#   }

package mcp.authz

import future.keywords.if
import future.keywords.in

# ──────────────────────────────────────────
# 기본값: 거부 (fail-closed)
# ──────────────────────────────────────────
default allow := false

# ──────────────────────────────────────────
# admin: 모든 리소스 허용 (단, 업무 시간 외 민감 리소스 제한)
# ──────────────────────────────────────────
allow if {
    input.role == "admin"
    not is_off_hours_sensitive(input.resource, input.context.hour)
}

# admin도 새벽(02~05시)에 hr_data 접근은 차단
is_off_hours_sensitive(resource, hour) if {
    resource == "hr_data"
    hour >= 2
    hour < 5
}

# ──────────────────────────────────────────
# analyst: db_query, search_docs, get_weather 허용
#          단, hr 관련 테이블 직접 쿼리 차단
# ──────────────────────────────────────────
allow if {
    input.role == "analyst"
    input.resource in {"db_query", "search_docs", "get_weather"}
    not is_hr_query(input.context)
    not is_off_hours(input.context.hour)
}

is_hr_query(ctx) if {
    # context.table 필드가 있고 HR 관련 테이블인 경우
    ctx.table
    regex.match(`(?i)(hr_|employee|salary|payroll)`, ctx.table)
}

# ──────────────────────────────────────────
# viewer: 읽기 전용 도구만 허용
# ──────────────────────────────────────────
allow if {
    input.role == "viewer"
    input.resource in {"search_docs", "get_weather"}
    input.action == "execute"
}

# ──────────────────────────────────────────
# 업무 시간 외 (22시~06시) 고위험 작업 차단
# ──────────────────────────────────────────
high_risk_resources := {"db_query", "send_email", "hr_data"}

is_off_hours(hour) if {
    hour >= 22
}

is_off_hours(hour) if {
    hour < 6
}

# ──────────────────────────────────────────
# 감사 메타데이터 (항상 반환)
# ──────────────────────────────────────────
reason := msg if {
    allow
    msg := sprintf("allowed: role=%s resource=%s action=%s", [input.role, input.resource, input.action])
}

reason := msg if {
    not allow
    msg := sprintf("denied: role=%s resource=%s action=%s", [input.role, input.resource, input.action])
}

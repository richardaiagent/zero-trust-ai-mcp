# Chapter 4. MSA 구조 설계

> 서비스를 나누는 기준은 "기능"이 아니라 "변경의 이유"다. 같은 이유로 바뀌는 코드는 같은 서비스 안에 있어야 한다.

## 이 챕터에서 배우는 것

- MSA 서비스 경계를 긋는 기준 (도메인 분리 원칙)
- 각 서비스의 책임 범위와 데이터 스토어 분리 전략
- 서비스 간 통신 패턴 (동기 vs 비동기)
- Docker Compose로 전체 서비스를 로컬에서 실행하는 구조

## 사전 지식

> Chapter 3의 API 스펙을 기반으로 서비스 경계를 확정한다.  
> Docker 기본 개념(컨테이너, 이미지, 네트워크)이 필요하다.

---

## 4-1. 서비스 분리 기준

MSA에서 가장 어려운 결정은 "어디서 서비스를 나눌 것인가"다.

기준은 하나다 — **변경의 이유(Reason to Change)** 가 다르면 다른 서비스다.

| 서비스 | 변경이 일어나는 이유 |
|---|---|
| Gateway | 인증 방식 변경, Rate Limit 정책 변경, 라우팅 규칙 변경 |
| Orchestrator | AI 플로우 변경, 새 모델 추가, 의도 분류 로직 개선 |
| Policy Engine | 보안 정책 변경, 컴플라이언스 요건 변경 |
| Context Service | 세션 관리 전략 변경, 메모리 구조 변경 |
| RAG Service | 임베딩 모델 변경, 벡터 DB 교체, 검색 알고리즘 개선 |
| Tool Server | 새 외부 시스템 연동, Tool 추가/변경 |
| Audit Service | 로그 포맷 변경, 감사 요건 변경 |

이 7개 서비스가 이 프로젝트의 MSA 단위다.

---

## 4-2. 전체 서비스 맵

```mermaid
graph TB
    subgraph "공개 계층 (Public)"
        GW[Gateway<br/>:8000<br/>FastAPI]
    end

    subgraph "오케스트레이션 계층"
        ORCH[Orchestrator<br/>:8001<br/>FastAPI]
        PE[Policy Engine<br/>:8002<br/>FastAPI + OPA]
    end

    subgraph "실행 계층"
        TOOL[Tool Server<br/>:8003<br/>FastAPI]
        RAG[RAG Service<br/>:8004<br/>FastAPI]
        CTX[Context Service<br/>:8005<br/>FastAPI]
    end

    subgraph "수집 계층"
        AUDIT[Audit Service<br/>:8006<br/>FastAPI]
    end

    subgraph "데이터 스토어"
        REDIS[(Redis<br/>:6379<br/>세션 캐시)]
        PG[(PostgreSQL<br/>:5432<br/>사용자·감사 DB)]
        QDRANT[(Qdrant<br/>:6333<br/>벡터 DB)]
    end

    subgraph "메시지"
        PUBSUB[Redis Pub/Sub<br/>감사 이벤트 채널]
    end

    GW --> ORCH
    ORCH --> PE
    ORCH --> TOOL
    ORCH --> RAG
    ORCH --> CTX
    GW --> PUBSUB
    ORCH --> PUBSUB
    AUDIT --> PUBSUB
    CTX --> REDIS
    CTX --> PG
    AUDIT --> PG
    RAG --> QDRANT

    style GW fill:#e74c3c,color:#fff
    style PE fill:#c0392b,color:#fff
    style AUDIT fill:#27ae60,color:#fff
```

---

## 4-3. 데이터 스토어 분리 전략

MSA의 핵심 원칙 중 하나는 **서비스별 데이터 스토어 소유권**이다.  
여러 서비스가 같은 DB 테이블을 공유하면, 하나의 서비스가 바뀔 때 다른 서비스가 깨진다.

| 서비스 | 데이터 스토어 | 저장 데이터 |
|---|---|---|
| Context Service | Redis | 대화 히스토리, 세션 TTL |
| Context Service | PostgreSQL | 사용자 프로파일, 장기 설정 |
| Audit Service | PostgreSQL | 감사 이벤트 로그 |
| RAG Service | Qdrant | 문서 임베딩 벡터 |
| Tool Server | 없음 (외부 시스템 직접 호출) | — |
| Policy Engine | 파일 (OPA 정책 파일) | 정책 규칙 YAML |

### 🔥 핵심 포인트

PostgreSQL을 두 서비스(Context, Audit)가 공유하지만, **스키마(Schema)를 분리**해서 격리한다.

```sql
-- PostgreSQL 스키마 분리
CREATE SCHEMA context_svc;   -- Context Service 전용
CREATE SCHEMA audit_svc;     -- Audit Service 전용

-- 각 서비스는 자신의 스키마에만 접근 권한 부여
GRANT ALL ON SCHEMA context_svc TO context_user;
GRANT ALL ON SCHEMA audit_svc TO audit_user;
REVOKE ALL ON SCHEMA context_svc FROM audit_user;
REVOKE ALL ON SCHEMA audit_svc FROM context_user;
```

---

## 4-4. 서비스 간 통신 패턴

### 동기 통신 (요청-응답)

시간이 중요한 흐름 — Gateway → Orchestrator → Tool/RAG/Context — 은 동기 HTTP다.  
요청이 완료될 때까지 기다려야 사용자에게 응답할 수 있기 때문이다.

```python
# src/orchestrator/app/clients/tool_client.py

import httpx
from app.config import settings

class ToolClient:
    def __init__(self):
        self.base_url = settings.TOOL_SERVER_URL
        self.secret = settings.SERVICE_SECRET

    async def execute(self, tool_name: str, parameters: dict, user_id: str, role: str) -> dict:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{self.base_url}/tools/{tool_name}/execute",
                json={"user_id": user_id, "role": role, "parameters": parameters},
                headers={"X-Service-Secret": self.secret},
            )
            response.raise_for_status()
            return response.json()
```

### 비동기 통신 (이벤트 발행)

감사 로그는 응답 시간에 영향을 주면 안 된다.  
**Redis Pub/Sub**로 이벤트를 발행하고, Audit Service가 구독해서 저장한다.

```python
# src/shared/audit_publisher.py

import json
import redis.asyncio as aioredis
from datetime import datetime

class AuditPublisher:
    CHANNEL = "mcp:audit:events"

    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client

    async def publish(self, event_type: str, payload: dict, trace_id: str):
        event = {
            "event_type": event_type,
            "payload": payload,
            "trace_id": trace_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self.redis.publish(self.CHANNEL, json.dumps(event))

# Audit Service 구독자
# src/audit-service/app/subscriber.py

class AuditSubscriber:
    async def listen(self, redis_client: aioredis.Redis, db_session):
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(AuditPublisher.CHANNEL)

        async for message in pubsub.listen():
            if message["type"] == "message":
                event = json.loads(message["data"])
                await self._save(event, db_session)

    async def _save(self, event: dict, db_session):
        await db_session.execute(
            """INSERT INTO audit_svc.events
               (event_type, payload, trace_id, recorded_at)
               VALUES (:event_type, :payload, :trace_id, NOW())""",
            event,
        )
```

```mermaid
sequenceDiagram
    participant GW as Gateway
    participant ORCH as Orchestrator
    participant PUBSUB as Redis Pub/Sub
    participant AUDIT as Audit Service

    GW->>ORCH: 요청 전달
    GW->>PUBSUB: publish("request_received", {...})
    Note over GW,PUBSUB: 비동기 — 응답 기다리지 않음

    ORCH->>ORCH: 처리 중...
    ORCH->>PUBSUB: publish("tool_executed", {...})

    PUBSUB-->>AUDIT: 이벤트 수신
    AUDIT->>AUDIT: DB 저장

    ORCH-->>GW: 응답 반환 (Audit 완료 여부와 무관)
```

---

## 4-5. 프로젝트 디렉토리 구조

```
zero-trust-ai-mcp/
├── src/
│   ├── gateway/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── app/
│   │       ├── main.py
│   │       ├── config.py
│   │       ├── routers/
│   │       │   └── v1/
│   │       │       └── chat.py
│   │       ├── middleware/
│   │       │   ├── auth.py
│   │       │   └── rate_limit.py
│   │       ├── clients/
│   │       │   └── orchestrator.py
│   │       └── schemas/
│   │           └── chat.py
│   │
│   ├── orchestrator/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── app/
│   │       ├── main.py
│   │       ├── config.py
│   │       ├── core/
│   │       │   ├── flow.py          ← 핵심 오케스트레이션 로직
│   │       │   └── router.py        ← 모델 라우팅
│   │       ├── routers/
│   │       │   └── internal.py
│   │       └── clients/
│   │           ├── tool_client.py
│   │           ├── rag_client.py
│   │           └── context_client.py
│   │
│   ├── policy-engine/
│   ├── context-service/
│   ├── rag-service/
│   ├── tool-service/
│   └── audit-service/
│
├── shared/                          ← 서비스 간 공유 코드
│   ├── schemas/
│   │   └── error.py
│   └── audit_publisher.py
│
├── infra/
│   ├── docker-compose.yml           ← 로컬 개발 환경
│   ├── docker-compose.prod.yml      ← 운영 오버라이드
│   ├── helm/                        ← K8s Helm Chart
│   └── k8s/                         ← K8s 매니페스트
│
└── .env.example                     ← 환경변수 템플릿
```

---

## 4-6. Docker Compose 구성

로컬 개발 환경에서 전체 서비스를 한 번에 올리는 설정이다.

```yaml
# infra/docker-compose.yml

version: "3.9"

networks:
  mcp-net:
    driver: bridge

volumes:
  postgres-data:
  qdrant-data:

services:
  # ── 데이터 스토어 ──────────────────────────────
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    networks: [mcp-net]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: mcp_db
      POSTGRES_USER: mcp_admin
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports: ["5432:5432"]
    volumes: ["postgres-data:/var/lib/postgresql/data"]
    networks: [mcp-net]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mcp_admin"]
      interval: 5s

  qdrant:
    image: qdrant/qdrant:latest
    ports: ["6333:6333"]
    volumes: ["qdrant-data:/qdrant/storage"]
    networks: [mcp-net]

  # ── MCP 서비스 ─────────────────────────────────
  gateway:
    build: ../src/gateway
    ports: ["8000:8000"]
    env_file: ../.env
    environment:
      ORCHESTRATOR_URL: http://orchestrator:8001
      REDIS_URL: redis://redis:6379
    depends_on:
      redis: {condition: service_healthy}
    networks: [mcp-net]

  orchestrator:
    build: ../src/orchestrator
    ports: ["8001:8001"]
    env_file: ../.env
    environment:
      TOOL_SERVER_URL: http://tool-service:8003
      RAG_SERVICE_URL: http://rag-service:8004
      CONTEXT_SERVICE_URL: http://context-service:8005
      POLICY_ENGINE_URL: http://policy-engine:8002
    depends_on: [gateway]
    networks: [mcp-net]

  policy-engine:
    build: ../src/policy-engine
    ports: ["8002:8002"]
    env_file: ../.env
    networks: [mcp-net]

  tool-service:
    build: ../src/tool-service
    ports: ["8003:8003"]
    env_file: ../.env
    networks: [mcp-net]

  rag-service:
    build: ../src/rag-service
    ports: ["8004:8004"]
    env_file: ../.env
    environment:
      QDRANT_URL: http://qdrant:6333
    depends_on: [qdrant]
    networks: [mcp-net]

  context-service:
    build: ../src/context-service
    ports: ["8005:8005"]
    env_file: ../.env
    environment:
      REDIS_URL: redis://redis:6379
      DB_URL: postgresql://mcp_admin:${POSTGRES_PASSWORD}@postgres:5432/mcp_db
    depends_on:
      redis: {condition: service_healthy}
      postgres: {condition: service_healthy}
    networks: [mcp-net]

  audit-service:
    build: ../src/audit-service
    ports: ["8006:8006"]
    env_file: ../.env
    environment:
      REDIS_URL: redis://redis:6379
      DB_URL: postgresql://mcp_admin:${POSTGRES_PASSWORD}@postgres:5432/mcp_db
    depends_on:
      redis: {condition: service_healthy}
      postgres: {condition: service_healthy}
    networks: [mcp-net]
```

⚠️ **주의사항**: `depends_on`은 컨테이너 **시작 순서**만 보장하지, 서비스가 **준비(ready)** 됐는지는 보장하지 않는다.  
`condition: service_healthy`와 함께 `healthcheck`를 반드시 설정해야 한다.

---

## 4-7. 환경변수 관리

```bash
# .env.example — 이 파일을 .env로 복사하고 실제 값을 채운다
# 절대 .env 파일을 git에 커밋하지 말 것

# ── LLM API ──────────────────────────────
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# ── 서비스 간 인증 ─────────────────────────
SERVICE_SECRET=your-strong-random-secret-here

# ── JWT ──────────────────────────────────
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# ── DB ───────────────────────────────────
POSTGRES_PASSWORD=your-db-password

# ── Rate Limit ───────────────────────────
RATE_LIMIT_PER_MINUTE=20
MONTHLY_TOKEN_QUOTA=10000000
```

```python
# src/shared/config.py — Pydantic Settings로 환경변수 로드

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    anthropic_api_key: str
    service_secret: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    rate_limit_per_minute: int = 20
    monthly_token_quota: int = 10_000_000

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

### 🔥 핵심 포인트

`pydantic-settings`는 환경변수가 없으면 앱 시작 시 즉시 에러를 낸다.  
운영 환경에서 "왜 이 기능이 안 되지?"를 디버깅하다가 환경변수가 빠진 걸 발견하는 상황을 방지한다.

---

## 정리

| 항목 | 결정 사항 |
|---|---|
| 서비스 수 | 7개 (Gateway, Orchestrator, Policy Engine, Context, RAG, Tool, Audit) |
| 분리 기준 | 변경의 이유(Reason to Change) |
| 데이터 스토어 | Redis(세션), PostgreSQL(사용자·감사), Qdrant(벡터) |
| 동기 통신 | HTTP REST (Gateway → Orchestrator → 실행 서비스) |
| 비동기 통신 | Redis Pub/Sub (감사 이벤트) |
| 로컬 실행 | Docker Compose + healthcheck |

---

## 다음 챕터 예고

> Chapter 5에서는 실제로 이 환경을 Windows 11에 구성한다.  
> Docker Desktop, Podman, Minikube 설치부터 첫 서비스 기동까지 단계별로 따라간다.

---
name: code
description: 실습 소스코드를 생성할 때 사용하는 스킬. "코드 만들어줘", "구현해줘", "FastAPI 작성", "서비스 코드", "API 코드 생성" 등의 요청에 반드시 사용. Gateway/Orchestrator/RAG/Tool/Policy/Audit 서비스 코드 생성 모두 해당.
---

# 코드 생성 스킬

## 역할
이 스킬은 MCP 플랫폼의 각 마이크로서비스 코드를
일관된 구조와 품질로 생성한다.

---

## 서비스별 디렉토리 구조

### FastAPI 서비스 기본 구조
```
src/{service-name}/
├── app/
│   ├── main.py            ← FastAPI 앱 진입점
│   ├── routes/            ← API 라우터
│   │   └── {resource}.py
│   ├── service/           ← 비즈니스 로직
│   │   └── {name}_service.py
│   ├── repository/        ← DB/Redis 접근
│   │   └── {name}_repo.py
│   ├── models/            ← Pydantic 모델
│   │   └── schemas.py
│   ├── clients/           ← 타 서비스 호출
│   │   └── {service}_client.py
│   └── config/
│       └── settings.py
├── tests/
│   └── test_{name}.py
├── Dockerfile
└── requirements.txt
```

---

## 코드 품질 규칙

### 필수 포함 항목
- **타입 힌트**: 모든 함수 파라미터/반환값
- **Pydantic 모델**: 요청/응답 스키마 분리
- **에러 핸들링**: try/except + HTTPException
- **로깅**: 요청/응답 기본 로그
- **환경변수**: settings.py 통해 관리

### 금지 사항
- 하드코딩된 URL, 비밀번호, API Key
- 타입 힌트 없는 함수
- 에러 핸들링 없는 외부 호출
- 동기 코드로 비동기 처리 (async/await 혼용 주의)

---

## 파일 헤더 템플릿

```python
# src/{service}/app/{파일경로}
# 역할: {이 파일의 역할 한 줄}
# 관련 챕터: Chapter N

from typing import Optional
from fastapi import APIRouter, HTTPException
# ... imports
```

---

## 서비스별 핵심 패턴

### Gateway (진입점)
```python
# src/gateway/app/routes/chat.py
from fastapi import APIRouter, Depends, HTTPException
from app.middleware.auth import verify_token
from app.clients.orchestrator_client import OrchestratorClient
from app.models.schemas import ChatRequest, ChatResponse

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    token: dict = Depends(verify_token)
) -> ChatResponse:
    try:
        result = await OrchestratorClient.chat(req)
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Orchestrator (핵심 로직)
```python
# src/orchestrator/app/service/chat_service.py
# 1. 정책 체크 → 2. 캐시 확인 → 3. Context → 4. RAG
# → 5. Tool → 6. Prompt 구성 → 7. LLM → 8. 캐싱
```

### 환경변수 관리
```python
# src/{service}/app/config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    redis_host: str = "localhost"
    redis_port: int = 6379
    db_host: str = "localhost"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

---

## Spring Boot 참고 코드 규칙

FastAPI 코드 이후 별도 섹션으로 추가:

```
### Spring Boot 참고 (Java)
> FastAPI 구현과 동일한 로직의 Java 버전입니다.
```

---

## Dockerfile 템플릿

```dockerfile
# src/{service}/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

---

## requirements.txt 기본 구성

```
fastapi==0.111.0
uvicorn==0.29.0
pydantic==2.7.0
pydantic-settings==2.3.0
httpx==0.27.0
redis==5.0.4
sqlalchemy==2.0.30
asyncpg==0.29.0
python-jose==3.3.0
```

---

## 출력 규칙

1. 파일 경로 주석 항상 첫 줄에
2. 코드 이후 "실행 방법" 명시
3. Windows 환경 고려 (경로, 환경변수 설정법)
4. 연관 파일 있으면 함께 생성

---

## 실행 방법 템플릿 (Windows)

```bash
# 로컬 실행 (Windows PowerShell)
cd src/gateway
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080

# Docker 실행
docker build -t mcp-gateway .
docker run -p 8080:8080 --env-file .env mcp-gateway

# Podman 실행 (Gateway 배포)
podman build -t mcp-gateway .
podman run -p 8080:8080 --env-file .env mcp-gateway
```

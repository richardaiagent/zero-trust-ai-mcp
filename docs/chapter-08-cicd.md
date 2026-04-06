# Chapter 8. CI/CD 파이프라인

> 배포를 손으로 하는 순간, 실수와 환경 차이가 생긴다. 파이프라인은 그 실수를 없애는 도구다.

## 이 챕터에서 배우는 것

- GitLab CI/CD 파이프라인 전체 구성 (빌드 → 테스트 → 배포)
- 서비스별 변경 감지로 필요한 서비스만 빌드하는 최적화
- ArgoCD GitOps 연동으로 K8s 배포 자동화
- 파이프라인 보안 — 시크릿 관리 및 이미지 취약점 스캔

## 사전 지식

> Chapter 7의 Helm Chart 구조를 알고 있어야 한다.  
> GitLab, Docker Registry, K8s 기본 개념이 필요하다.

---

## 8-1. CI/CD 전체 흐름

```mermaid
flowchart LR
    DEV[개발자 코드 Push] --> GL[GitLab Repository]
    GL --> CI[GitLab CI Pipeline]

    subgraph CI["GitLab CI Pipeline"]
        direction TB
        S1[① Lint & 단위 테스트] --> S2[② 변경 서비스 감지]
        S2 --> S3[③ Docker 이미지 빌드]
        S3 --> S4[④ 취약점 스캔]
        S4 --> S5[⑤ 통합 테스트]
        S5 --> S6[⑥ values.yaml 업데이트]
    end

    S6 --> GITOPS[GitOps Repository]
    GITOPS --> ARGO[ArgoCD]
    ARGO --> K8S[K8s 클러스터 자동 배포]

    style CI fill:#f0f0f0
    style ARGO fill:#27ae60,color:#fff
```

### 🔥 핵심 포인트

이 파이프라인에서 중요한 설계 결정이 하나 있다.  
**애플리케이션 코드 저장소**와 **K8s 배포 설정 저장소를 분리**한다.  
이것이 GitOps 패턴의 핵심이다. ArgoCD는 배포 설정 저장소만 바라본다.

---

## 8-2. GitLab CI/CD 파이프라인 전체 파일

```yaml
# .gitlab-ci.yml (프로젝트 루트)

stages:
  - lint
  - detect
  - build
  - scan
  - test
  - deploy

variables:
  REGISTRY: registry.gitlab.com/$CI_PROJECT_NAMESPACE/$CI_PROJECT_NAME
  IMAGE_TAG: $CI_COMMIT_SHORT_SHA
  PYTHON_VERSION: "3.12"

# ── 캐시 설정 ───────────────────────────────────
.python-cache: &python-cache
  cache:
    key:
      files:
        - "**/requirements.txt"
    paths:
      - .pip-cache/

# ── 1단계: Lint & 단위 테스트 ───────────────────
lint:
  stage: lint
  image: python:3.12-slim
  <<: *python-cache
  before_script:
    - pip install ruff black --quiet --cache-dir .pip-cache
  script:
    - ruff check src/ shared/
    - black --check src/ shared/
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main"

unit-test:
  stage: lint
  image: python:3.12-slim
  <<: *python-cache
  services:
    - redis:7-alpine
  variables:
    REDIS_URL: redis://redis:6379
    JWT_SECRET_KEY: test-secret
    SERVICE_SECRET: test-service-secret
  before_script:
    - pip install pytest pytest-asyncio httpx --cache-dir .pip-cache
    - pip install -r src/gateway/requirements.txt --cache-dir .pip-cache
  script:
    - pytest tests/unit/ -v --tb=short
  coverage: '/TOTAL.*\s(\d+%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

# ── 2단계: 변경된 서비스 감지 ────────────────────
detect-changes:
  stage: detect
  image: alpine/git:latest
  script:
    - |
      CHANGED=""
      for SVC in gateway orchestrator policy-engine context-service rag-service tool-service audit-service; do
        if git diff --name-only HEAD~1 HEAD | grep -q "src/$SVC/"; then
          CHANGED="$CHANGED $SVC"
        fi
      done
      echo "CHANGED_SERVICES=$CHANGED" >> changed.env
      echo "변경 감지된 서비스: $CHANGED"
  artifacts:
    reports:
      dotenv: changed.env
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

# ── 3단계: Docker 이미지 빌드 ────────────────────
.build-template: &build-template
  stage: build
  image: docker:26
  services:
    - docker:26-dind
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

build-gateway:
  <<: *build-template
  script:
    - |
      if echo "$CHANGED_SERVICES" | grep -q "gateway"; then
        docker build -t $REGISTRY/mcp-gateway:$IMAGE_TAG src/gateway/
        docker push $REGISTRY/mcp-gateway:$IMAGE_TAG
        docker tag $REGISTRY/mcp-gateway:$IMAGE_TAG $REGISTRY/mcp-gateway:latest
        docker push $REGISTRY/mcp-gateway:latest
      else
        echo "gateway 변경 없음, 빌드 스킵"
      fi
  needs: ["detect-changes"]

build-orchestrator:
  <<: *build-template
  script:
    - |
      if echo "$CHANGED_SERVICES" | grep -q "orchestrator"; then
        docker build -t $REGISTRY/mcp-orchestrator:$IMAGE_TAG src/orchestrator/
        docker push $REGISTRY/mcp-orchestrator:$IMAGE_TAG
      else
        echo "orchestrator 변경 없음, 빌드 스킵"
      fi
  needs: ["detect-changes"]

# (나머지 서비스도 동일 패턴으로 추가)

# ── 4단계: 취약점 스캔 ──────────────────────────
trivy-scan:
  stage: scan
  image:
    name: aquasec/trivy:latest
    entrypoint: [""]
  script:
    - |
      for SVC in gateway orchestrator; do
        echo "🔍 Scanning $SVC..."
        trivy image \
          --exit-code 1 \
          --severity HIGH,CRITICAL \
          --no-progress \
          $REGISTRY/mcp-$SVC:$IMAGE_TAG
      done
  allow_failure: false
  needs: ["build-gateway", "build-orchestrator"]
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

# ── 5단계: 통합 테스트 ──────────────────────────
integration-test:
  stage: test
  image: python:3.12-slim
  services:
    - name: redis:7-alpine
      alias: redis
    - name: $REGISTRY/mcp-gateway:$IMAGE_TAG
      alias: gateway
      variables:
        ORCHESTRATOR_URL: "http://mock-orchestrator:8001"
        REDIS_URL: "redis://redis:6379"
        JWT_SECRET_KEY: "test-secret"
        SERVICE_SECRET: "test-service-secret"
  variables:
    GATEWAY_URL: http://gateway:8000
  before_script:
    - pip install httpx pytest pytest-asyncio --quiet
  script:
    - pytest tests/integration/ -v --timeout=30
  needs: ["trivy-scan"]
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

# ── 6단계: GitOps 저장소 업데이트 ────────────────
update-gitops:
  stage: deploy
  image: alpine/git:latest
  before_script:
    - git config --global user.email "ci@gitlab.com"
    - git config --global user.name "GitLab CI"
    - git clone https://oauth2:$GITOPS_TOKEN@gitlab.com/$GITOPS_REPO gitops-repo
  script:
    - cd gitops-repo
    - |
      # Helm values.yaml의 imageTag 업데이트
      sed -i "s|imageTag:.*|imageTag: \"$IMAGE_TAG\"|g" \
        infra/helm/mcp-platform/values-dev.yaml
    - git add infra/helm/mcp-platform/values-dev.yaml
    - git commit -m "ci: update image tag to $IMAGE_TAG [skip ci]"
    - git push
  needs: ["integration-test"]
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

---

## 8-3. 단위 테스트 예시

파이프라인이 실행할 테스트 코드를 작성한다.

```python
# tests/unit/gateway/test_rate_limiter.py

import pytest
import fakeredis.aioredis as fakeredis
from app.middleware.rate_limit import RateLimiter
from fastapi import HTTPException
from unittest.mock import MagicMock

@pytest.fixture
def redis():
    return fakeredis.FakeRedis(decode_responses=True)

@pytest.fixture
def request_mock(redis):
    req = MagicMock()
    req.app.state.redis = redis
    return req

@pytest.mark.asyncio
async def test_rate_limit_allows_within_limit(request_mock):
    """분당 20회 제한 이내 요청은 통과해야 한다"""
    limiter = RateLimiter()
    for _ in range(20):
        await limiter.check(request_mock, user_id="user-001")  # 예외 없이 통과

@pytest.mark.asyncio
async def test_rate_limit_blocks_over_limit(request_mock):
    """분당 21회 초과 시 429 에러를 반환해야 한다"""
    limiter = RateLimiter()
    for _ in range(20):
        await limiter.check(request_mock, user_id="user-002")

    with pytest.raises(HTTPException) as exc_info:
        await limiter.check(request_mock, user_id="user-002")
    assert exc_info.value.status_code == 429

@pytest.mark.asyncio
async def test_rate_limit_isolated_per_user(request_mock):
    """서로 다른 user_id는 독립적으로 카운트된다"""
    limiter = RateLimiter()
    for _ in range(20):
        await limiter.check(request_mock, user_id="user-A")

    # user-B는 별개 카운터이므로 통과
    await limiter.check(request_mock, user_id="user-B")
```

```python
# tests/unit/gateway/test_auth.py

import pytest
from jose import jwt
from datetime import datetime, timedelta
from app.middleware.auth import verify_token
from app.config import settings
from fastapi import HTTPException
from unittest.mock import MagicMock

def make_token(sub: str = "user-001", role: str = "analyst", expire_delta: int = 60) -> str:
    payload = {
        "sub": sub,
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=expire_delta),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

@pytest.mark.asyncio
async def test_valid_token_passes():
    token = make_token()
    creds = MagicMock(credentials=token)
    result = await verify_token(creds)
    assert result["sub"] == "user-001"
    assert result["role"] == "analyst"

@pytest.mark.asyncio
async def test_expired_token_raises_401():
    token = make_token(expire_delta=-1)  # 만료된 토큰
    creds = MagicMock(credentials=token)
    with pytest.raises(HTTPException) as exc:
        await verify_token(creds)
    assert exc.value.status_code == 401
```

---

## 8-4. ArgoCD GitOps 연동

ArgoCD는 GitOps 저장소의 변경을 감지하고 K8s에 자동으로 반영한다.

```yaml
# infra/k8s/argocd-app.yaml
# ArgoCD Application 리소스 정의

apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: mcp-platform-dev
  namespace: argocd
spec:
  project: default

  source:
    repoURL: https://gitlab.com/your-org/mcp-platform-gitops
    targetRevision: HEAD
    path: infra/helm/mcp-platform
    helm:
      valueFiles:
        - values-dev.yaml

  destination:
    server: https://kubernetes.default.svc
    namespace: mcp-dev

  syncPolicy:
    automated:
      prune: true       # 삭제된 리소스 자동 정리
      selfHeal: true    # 수동 변경을 자동으로 원복
    syncOptions:
      - CreateNamespace=true
      - PrunePropagationPolicy=foreground
    retry:
      limit: 3
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
```

```bash
# ArgoCD CLI로 설치 및 앱 등록 (서버에서 실행)

# ArgoCD 설치
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# 초기 admin 비밀번호 확인
kubectl get secret argocd-initial-admin-secret -n argocd \
  -o jsonpath="{.data.password}" | base64 -d

# ArgoCD CLI 로그인
argocd login localhost:8080 --username admin --password <위 비밀번호>

# Application 등록
kubectl apply -f infra/k8s/argocd-app.yaml

# 동기화 상태 확인
argocd app get mcp-platform-dev
argocd app sync mcp-platform-dev
```

---

## 8-5. 파이프라인 시크릿 관리

GitLab CI에서 민감한 값은 **CI/CD Variables**로 관리한다.  
절대 `.gitlab-ci.yml` 파일에 직접 값을 쓰지 않는다.

```mermaid
graph LR
    DEV[개발자] -->|수동 등록| GLVAR[GitLab CI/CD Variables]
    GLVAR -->|파이프라인 실행 시 주입| CI[CI Runner]
    CI -->|이미지 푸시| REG[Container Registry]
    CI -->|gitops repo 업데이트| GITOPS[GitOps Repo]
    GITOPS --> ARGO[ArgoCD]
    ARGO -->|K8s Secret 생성| K8S[K8s Cluster]
```

GitLab CI/CD Variables에 등록해야 할 항목:

| 변수명 | 설명 | Masked | Protected |
|---|---|:---:|:---:|
| `CI_REGISTRY_USER` | GitLab Registry 사용자명 | ✅ | ✅ |
| `CI_REGISTRY_PASSWORD` | GitLab Registry 비밀번호 | ✅ | ✅ |
| `GITOPS_TOKEN` | GitOps 저장소 접근 토큰 | ✅ | ✅ |
| `GITOPS_REPO` | GitOps 저장소 경로 | ❌ | ✅ |

⚠️ **주의사항**: `Masked` 설정을 켜면 파이프라인 로그에 값이 `[MASKED]`로 표시된다.  
하지만 `echo $SECRET_VAR > file.txt` 처럼 파일에 쓰면 마스킹이 우회된다.  
시크릿을 파일로 절대 덤프하지 말 것.

---

## 8-6. Merge Request 파이프라인 전략

```mermaid
graph TD
    MR[Merge Request 생성] --> LINT[Lint + 단위 테스트]
    LINT --> REVIEW[코드 리뷰]
    REVIEW --> APPROVE{승인?}
    APPROVE -->|No| FIX[수정 후 재Push]
    APPROVE -->|Yes| MERGE[main 브랜치 Merge]
    MERGE --> FULL[전체 파이프라인 실행]
    FULL --> DEV[dev 환경 자동 배포]
    DEV --> MANUAL{수동 승인}
    MANUAL --> PROD[prod 환경 배포]
```

```yaml
# .gitlab-ci.yml에 추가 — 운영 배포는 수동 승인 필요

deploy-prod:
  stage: deploy
  image: alpine/git:latest
  script:
    - cd gitops-repo
    - sed -i "s|imageTag:.*|imageTag: \"$IMAGE_TAG\"|g" \
        infra/helm/mcp-platform/values-prod.yaml
    - git add . && git commit -m "ci: deploy $IMAGE_TAG to prod"
    - git push
  when: manual           # 수동 실행
  environment:
    name: production
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

---

## 정리

| 항목 | 내용 |
|---|---|
| 파이프라인 단계 | lint → 변경감지 → build → scan → 통합테스트 → GitOps 업데이트 |
| 빌드 최적화 | 변경된 서비스만 빌드 (git diff 기반 감지) |
| 보안 스캔 | Trivy로 HIGH/CRITICAL 취약점 차단 |
| GitOps | 코드 저장소 ↔ 배포 저장소 분리, ArgoCD 자동 동기화 |
| 시크릿 | GitLab CI/CD Variables (Masked + Protected) |
| 운영 배포 | 수동 승인 (`when: manual`) 필수 |

---

## 다음 챕터 예고

> Chapter 9에서는 보안 아키텍처를 심화한다.  
> mTLS 서비스 간 통신 암호화, Network Policy로 서비스 격리,  
> OPA 정책 엔진 상세 설정을 다룬다.

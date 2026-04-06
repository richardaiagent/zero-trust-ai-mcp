---
name: infra
description: 인프라 설정 파일을 생성할 때 사용하는 스킬. "Helm 만들어줘", "K8s YAML", "docker-compose", "Minikube 배포", "Podman 설정", "GitLab CI", "ArgoCD", "인프라 구성" 등의 요청에 반드시 사용.
---

# 인프라 생성 스킬

## 역할
이 스킬은 MCP 플랫폼의 인프라 설정 파일을
실제 배포 가능한 수준으로 생성한다.

---

## 배포 환경 기준 (항상 이 환경 기준)

| 환경 | 도구 |
|---|---|
| 로컬 전체 실행 | Docker Desktop + docker-compose |
| Gateway 배포 | Podman (Linux 서버) |
| Orchestration | Minikube (로컬/서버) |
| 패키지 관리 | Helm |
| GitOps | ArgoCD |
| CI/CD | GitLab + GitLab Actions |

---

## 디렉토리 구조

```
infra/
├── docker-compose.yml          ← 로컬 전체 실행
├── helm/
│   ├── gateway/
│   │   ├── Chart.yaml
│   │   ├── values.yaml
│   │   └── templates/
│   │       ├── deployment.yaml
│   │       ├── service.yaml
│   │       ├── hpa.yaml
│   │       └── ingress.yaml
│   └── orchestrator/
│       └── (동일 구조)
├── k8s/
│   ├── namespace.yaml
│   ├── network-policy.yaml
│   └── secret.yaml
└── gitlab/
    ├── .gitlab-ci.yml
    └── argocd-app.yaml
```

---

## Docker Compose 템플릿

```yaml
# infra/docker-compose.yml
version: '3.8'

services:
  gateway:
    build: ../src/gateway
    ports:
      - "8080:8080"
    environment:
      - ORCHESTRATOR_URL=http://orchestrator:8081
      - REDIS_HOST=redis
    depends_on:
      - redis
      - orchestrator
    networks:
      - mcp-net

  orchestrator:
    build: ../src/orchestrator
    ports:
      - "8081:8081"
    environment:
      - REDIS_HOST=redis
      - DB_HOST=postgres
      - VECTOR_DB_HOST=postgres
    depends_on:
      - redis
      - postgres
    networks:
      - mcp-net

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - mcp-net

  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: mcp_db
      POSTGRES_USER: mcp_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - mcp-net

networks:
  mcp-net:
    driver: bridge

volumes:
  postgres_data:
```

---

## Helm Chart 템플릿

### Chart.yaml
```yaml
# infra/helm/gateway/Chart.yaml
apiVersion: v2
name: mcp-gateway
description: MCP Gateway Helm Chart
type: application
version: 0.1.0
appVersion: "1.0.0"
```

### values.yaml
```yaml
# infra/helm/gateway/values.yaml
replicaCount: 3

image:
  repository: mcp-gateway
  tag: latest
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 80
  targetPort: 8080

resources:
  requests:
    cpu: 500m
    memory: 512Mi
  limits:
    cpu: "2"
    memory: 2Gi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

env:
  REDIS_HOST: redis
  DB_HOST: postgres
  LOG_LEVEL: INFO
```

### deployment.yaml
```yaml
# infra/helm/gateway/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-gateway
  namespace: mcp-system
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: {{ .Release.Name }}-gateway
  template:
    metadata:
      labels:
        app: {{ .Release.Name }}-gateway
    spec:
      serviceAccountName: gateway-sa
      containers:
        - name: gateway
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          ports:
            - containerPort: {{ .Values.service.targetPort }}
          envFrom:
            - configMapRef:
                name: {{ .Release.Name }}-config
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
          livenessProbe:
            httpGet:
              path: /health
              port: {{ .Values.service.targetPort }}
            initialDelaySeconds: 10
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /ready
              port: {{ .Values.service.targetPort }}
            initialDelaySeconds: 5
            periodSeconds: 5
```

---

## Podman 배포 (Gateway 전용)

```bash
# Linux 서버에서 Podman으로 Gateway 배포
# infra/podman/deploy-gateway.sh

#!/bin/bash
set -e

IMAGE_NAME="mcp-gateway"
CONTAINER_NAME="mcp-gateway"
PORT="8080"

echo "🔨 Building Gateway image..."
podman build -t ${IMAGE_NAME} ../../src/gateway/

echo "🛑 Stopping existing container..."
podman stop ${CONTAINER_NAME} 2>/dev/null || true
podman rm ${CONTAINER_NAME} 2>/dev/null || true

echo "🚀 Starting Gateway container..."
podman run -d \
  --name ${CONTAINER_NAME} \
  -p ${PORT}:8080 \
  --env-file .env \
  --restart=always \
  ${IMAGE_NAME}

echo "✅ Gateway deployed on port ${PORT}"
```

---

## Minikube 배포 (Orchestrator)

```bash
# Minikube 초기 세팅 (Windows PowerShell)
minikube start --cpus=4 --memory=8192 --driver=docker

# Namespace 생성
kubectl apply -f infra/k8s/namespace.yaml

# Helm으로 배포
helm upgrade --install mcp-orchestrator infra/helm/orchestrator \
  --namespace mcp-system \
  --values infra/helm/orchestrator/values.yaml

# 상태 확인
kubectl get pods -n mcp-system
```

---

## GitLab CI 템플릿

```yaml
# .gitlab-ci.yml
stages:
  - build
  - test
  - deploy-staging
  - deploy-prod

variables:
  DOCKER_DRIVER: overlay2
  IMAGE_REGISTRY: registry.gitlab.com/${CI_PROJECT_PATH}

build-gateway:
  stage: build
  script:
    - docker build -t ${IMAGE_REGISTRY}/gateway:${CI_COMMIT_SHA} src/gateway/
    - docker push ${IMAGE_REGISTRY}/gateway:${CI_COMMIT_SHA}
  only:
    - main
    - develop

test:
  stage: test
  script:
    - cd src/gateway && pip install -r requirements.txt
    - pytest tests/ -v --tb=short
  coverage: '/TOTAL.*\s+(\d+%)$/'

deploy-staging:
  stage: deploy-staging
  script:
    - helm upgrade --install mcp-gateway infra/helm/gateway
        --set image.tag=${CI_COMMIT_SHA}
        --namespace mcp-staging
  environment:
    name: staging
  only:
    - develop

deploy-prod:
  stage: deploy-prod
  script:
    - helm upgrade --install mcp-gateway infra/helm/gateway
        --set image.tag=${CI_COMMIT_SHA}
        --namespace mcp-system
  environment:
    name: production
  when: manual
  only:
    - main
```

---

## ArgoCD 앱 템플릿

```yaml
# infra/gitlab/argocd-app.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: mcp-platform
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://gitlab.com/{your-repo}/zero-trust-ai-mcp
    targetRevision: main
    path: infra/helm/orchestrator
  destination:
    server: https://kubernetes.default.svc
    namespace: mcp-system
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

---

## NetworkPolicy (Zero Trust)

```yaml
# infra/k8s/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-gateway-to-orchestrator
  namespace: mcp-system
spec:
  podSelector:
    matchLabels:
      app: orchestrator
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: gateway
      ports:
        - port: 8081
  policyTypes:
    - Ingress
```

---

## 출력 규칙

1. 파일 경로 주석 항상 첫 줄에
2. Windows PowerShell 기준 실행 명령어 포함
3. 환경변수는 `.env.example` 파일도 함께 생성
4. 보안 설정 (Secret, NetworkPolicy) 항상 포함
5. 실제 동작 확인 명령어 포함

---

## .env.example 템플릿

```bash
# .env.example — 실제 값으로 교체 후 .env로 복사
POSTGRES_PASSWORD=your_password_here
REDIS_PASSWORD=your_redis_password_here
JWT_SECRET=your_jwt_secret_here
OPENAI_API_KEY=your_openai_key_here
LLM_MODEL=gpt-4o
LOG_LEVEL=INFO
```

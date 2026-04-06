# 🚀 Zero Trust AI MCP — 실행 & 배포 가이드

> 작성자: 정상혁 (Sanghyuk Jung)  
> 환경 기준: Windows 11 (개인 PC) → Linux Ubuntu 22.04 (서버)

---

## ⚠️ 회사 컴퓨터에서 실행 전 반드시 읽을 것

> **이 프로젝트는 개인 시간, 개인 장비, 개인 비용으로 제작된 저작물입니다.**

회사 컴퓨터에서 실행할 경우 아래 리스크가 발생할 수 있습니다.

| 리스크 | 내용 |
|--------|------|
| 직무발명 주장 가능성 | 회사 장비 사용 이력이 남으면 회사가 소유권 주장 근거로 활용 가능 |
| 소스코드 유출 | 회사 보안솔루션(DLP)이 소스를 스캔·저장할 수 있음 |
| 네트워크 로그 | Docker 이미지 pull, API 키 사용 로그가 회사 망에 기록될 수 있음 |

### 🔒 회사 컴퓨터에서 안전하게 테스트하려면

- **소스코드는 USB 또는 개인 클라우드(개인 계정)로만 이동**
- **OPENAI_API_KEY 등 개인 API 키는 .env에만 — 절대 코드에 하드코딩 금지**
- **테스트 목적임을 명확히 — 업무 시간 외 개인 시간에 진행**
- **완료 후 소스, 이미지, 컨테이너 전부 삭제**
- **가능하면 개인 노트북으로 테스트 후 결과물만 회사 서버에 배포 권장**

---

## 📋 전체 실행 순서

```
STEP 1 → 로컬 실행 (Docker Desktop, Windows 11)
STEP 2 → Gateway 단독 배포 (Podman, Linux 서버)
STEP 3 → 전체 스택 배포 (Minikube + Helm, Linux 서버)
```

---

## STEP 1 — 로컬 실행 (Windows 11 + Docker Desktop)

### 사전 준비

| 도구 | 버전 | 설치 |
|------|------|------|
| Docker Desktop | 4.x 이상 | https://www.docker.com/products/docker-desktop |
| Python | 3.11 이상 | (선택 — 개별 서비스 로컬 실행 시) |
| VSCode | 최신 | https://code.visualstudio.com |

### 1-1. 환경변수 세팅


📋 첫 실행 순서 (다른 컴퓨터)
# 1. 프로젝트 루트에서 실행
.\scripts\setup-env.ps1

# 2. 각 .env 파일 열어서 시크릿 값 채우기
# (JWT_SECRET_KEY, SERVICE_SECRET, OPENAI_API_KEY, REDIS_PASSWORD, POSTGRES_PASSWORD)

# 3. 실행
docker compose -f infra/docker-compose.yml up -d



```powershell
# 프로젝트 루트로 이동
cd Q:\MY-LL_project\AirMcp\zero-trust-ai-mcp

# infra 공통 .env 생성
copy infra\.env.example infra\.env

# 각 서비스 .env 생성 (7개)
copy src\gateway\.env.example          src\gateway\.env
copy src\orchestrator\.env.example     src\orchestrator\.env
copy src\rag-service\.env.example      src\rag-service\.env
copy src\tool-service\.env.example     src\tool-service\.env
copy src\context-service\.env.example  src\context-service\.env
copy src\policy-engine\.env.example    src\policy-engine\.env
copy src\audit-service\.env.example    src\audit-service\.env
```

#### infra/.env 필수 값 채우기

```env
POSTGRES_USER=mcpuser
POSTGRES_PASSWORD=강력한_패스워드_입력
REDIS_PASSWORD=강력한_패스워드_입력
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=강력한_패스워드_입력
```

#### src/orchestrator/.env 필수 값 채우기

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx   # 개인 OpenAI API Key
```

### 1-2. 전체 빌드 & 기동

```powershell
# 전체 빌드 + 백그라운드 실행
docker compose -f infra/docker-compose.yml up -d --build

# 기동 상태 확인
docker compose -f infra/docker-compose.yml ps

# 헬스체크 (Gateway)
curl http://localhost:8000/healthz
```

### 1-3. 기동 순서 (자동 처리됨)

```
postgres, redis, qdrant, opa       ← 인프라 먼저 기동
         ↓ (healthcheck 통과 후)
policy-engine, audit-service, context-service, rag-service, tool-service
         ↓ (5개 서비스 모두 healthy 후)
orchestrator
         ↓
gateway                            ← 마지막 (외부 노출 포트 8000)
```

### 1-4. 접속 포인트

| 서비스 | URL | 용도 |
|--------|-----|------|
| Gateway API | http://localhost:8000 | 메인 API 진입점 |
| API 문서 (dev only) | http://localhost:8000/docs | Swagger UI |
| Grafana | http://localhost:3000 | 모니터링 대시보드 |
| Jaeger UI | http://localhost:16686 | 분산 추적 |
| Prometheus | http://localhost:9090 | 메트릭 수집 |

### 1-5. 토큰 발급 & API 테스트

```powershell
# 1. API 키로 JWT 토큰 발급
curl -X POST http://localhost:8000/v1/auth/token `
  -H "Content-Type: application/json" `
  -d '{"api_key": "dev-api-key-1234"}'

# 응답 예시:
# {"access_token": "eyJ...", "token_type": "bearer"}

# 2. 채팅 요청
$TOKEN = "eyJ..."

curl -X POST http://localhost:8000/v1/chat `
  -H "Authorization: Bearer $TOKEN" `
  -H "Content-Type: application/json" `
  -d '{"session_id": "test-001", "message": "안녕하세요"}'
```

### 1-6. 종료 & 정리

```powershell
# 컨테이너 중지
docker compose -f infra/docker-compose.yml down

# 볼륨까지 완전 삭제 (데이터 초기화)
docker compose -f infra/docker-compose.yml down -v

# 이미지까지 삭제 (회사 PC 정리 시 필수)
docker compose -f infra/docker-compose.yml down -v --rmi all
docker system prune -a
```

---

## STEP 2 — Gateway 단독 배포 (Linux 서버 + Podman)

> Gateway만 단독으로 Linux 서버에 Podman으로 배포.  
> 나머지 서비스는 로컬 또는 Minikube에서 실행 중인 상태 기준.

### 사전 준비 (서버)

```bash
# Ubuntu 22.04 기준 — Podman 설치
sudo apt-get update
sudo apt-get install -y podman

# 설치 확인
podman --version
```

### 2-1. 소스 서버로 복사

```powershell
# 개발 PC → 서버 (PowerShell)
scp -r src/gateway user@서버IP:/opt/mcp/gateway
scp src/gateway/.env user@서버IP:/opt/mcp/gateway/.env
```

### 2-2. Podman 빌드 & 실행

```bash
# 서버 SSH 접속 후
cd /opt/mcp/gateway

# 이미지 빌드
podman build -t mcp-gateway:0.1.0 .

# 컨테이너 실행
podman run -d \
  --name mcp-gateway \
  -p 8000:8000 \
  --env-file .env \
  --restart=always \
  mcp-gateway:0.1.0

# 확인
podman ps
curl http://localhost:8000/healthz
```

### 2-3. systemd 서비스 등록 (자동 재시작)

```bash
# systemd 서비스 파일 자동 생성
podman generate systemd --name mcp-gateway --files --new

# 서비스 등록
mkdir -p ~/.config/systemd/user/
mv container-mcp-gateway.service ~/.config/systemd/user/
systemctl --user enable container-mcp-gateway.service
systemctl --user start container-mcp-gateway.service

# 상태 확인
systemctl --user status container-mcp-gateway.service
```

---

## STEP 3 — 전체 스택 배포 (Minikube + Helm)

### 사전 준비 (Windows)

```powershell
# Minikube 설치
winget install Kubernetes.minikube

# kubectl 설치
winget install Kubernetes.kubectl

# Helm 설치
winget install Helm.Helm
```

### 3-1. Minikube 시작

```powershell
minikube start --cpus=4 --memory=8192 --driver=docker

# 상태 확인
minikube status
kubectl cluster-info
```

### 3-2. Namespace & Secret 생성

```powershell
# Namespace 생성
kubectl apply -f infra/k8s/namespace.yaml

# Secret 파일 준비
copy infra\k8s\secrets.example.yaml infra\k8s\secrets.yaml
# → secrets.yaml 열어서 CHANGE_ME 전부 실값으로 교체

# Secret 적용
kubectl apply -f infra/k8s/secrets.yaml -n mcp

# ⚠️ secrets.yaml 은 절대 git 커밋 금지
```

### 3-3. Helm 배포

```powershell
helm upgrade --install mcp-platform infra/helm/mcp-platform `
  --namespace mcp `
  --values infra/helm/mcp-platform/values.yaml `
  --create-namespace

# 상태 확인
kubectl get pods -n mcp
kubectl get svc -n mcp
```

### 3-4. Gateway 접속

```powershell
# NodePort URL 확인
minikube service mcp-gateway -n mcp --url

# 또는 포트포워딩
kubectl port-forward svc/mcp-gateway 8000:8080 -n mcp

# 헬스체크
curl http://localhost:8000/healthz
```

### 3-5. 업데이트 & 롤백

```powershell
# 이미지 태그 업데이트 후 재배포
helm upgrade mcp-platform infra/helm/mcp-platform `
  --namespace mcp `
  --set gateway.image.tag=0.2.0

# 롤백
helm rollback mcp-platform -n mcp

# 배포 히스토리
helm history mcp-platform -n mcp
```

### 3-6. 정리

```powershell
helm uninstall mcp-platform -n mcp
minikube stop
minikube delete   # 완전 초기화
```

---

## 🔧 트러블슈팅

### 컨테이너가 안 뜰 때

```powershell
docker compose -f infra/docker-compose.yml logs gateway
docker compose -f infra/docker-compose.yml logs orchestrator
```

### .env 값이 안 들어갈 때

```powershell
docker compose -f infra/docker-compose.yml exec gateway env | findstr OPENAI
```

### Minikube Pod이 Pending 상태일 때

```powershell
kubectl describe pod [pod명] -n mcp

# 리소스 부족이면 메모리 증설 후 재시작
minikube stop
minikube start --cpus=4 --memory=12288 --driver=docker
```

### API 401 Unauthorized

```
→ JWT 토큰 만료 확인 → /v1/auth/token 으로 재발급
→ Authorization: Bearer {토큰} 형식 확인 (Bearer 뒤 공백 1칸)
```

---

## 📋 체크리스트

### 로컬 실행 전

- [ ] Docker Desktop 실행 중
- [ ] infra/.env 작성 완료 (CHANGE_ME 없음)
- [ ] 각 서비스 .env 작성 완료 (7개)
- [ ] OPENAI_API_KEY 입력 완료
- [ ] .env 파일들 .gitignore 포함 확인

### 서버 배포 전

- [ ] secrets.yaml CHANGE_ME 없음
- [ ] secrets.yaml .gitignore 포함 확인
- [ ] 서버 방화벽 8000 포트 오픈
- [ ] Podman 또는 Minikube 설치 완료

### 회사 PC 테스트 후 (필수)

- [ ] `docker compose down -v --rmi all`
- [ ] .env 파일 전체 삭제 (API Key 포함)
- [ ] `docker system prune -a` 실행

---

*© 2025 정상혁 (Sanghyuk Jung). All Rights Reserved.*

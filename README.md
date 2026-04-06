# 📚 Zero Trust AI — MCP 기반 기업용 AI 플랫폼 설계

> **"개념부터 실전 배포까지, 기업 환경에서 살아남는 AI MCP 플랫폼 완전 정복"**

[![License](https://img.shields.io/badge/License-CC%20BY--NC--ND%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-nd/4.0/)
[![Chapters](https://img.shields.io/badge/Chapters-16-blue.svg)](./docs/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Main-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SpringBoot](https://img.shields.io/badge/Spring%20Boot-Reference-6DB33F?logo=springboot&logoColor=white)](https://spring.io/projects/spring-boot)
[![Docker](https://img.shields.io/badge/Docker-Required-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Kubernetes](https://img.shields.io/badge/Minikube-Orchestration-326CE5?logo=kubernetes&logoColor=white)](https://minikube.sigs.k8s.io/)
[![Podman](https://img.shields.io/badge/Podman-Gateway-892CA0?logo=podman&logoColor=white)](https://podman.io/)
[![Windows](https://img.shields.io/badge/Windows-11-0078D6?logo=windows&logoColor=white)](https://www.microsoft.com/windows)
[![GitLab](https://img.shields.io/badge/GitLab-CI%2FCD-FC6D26?logo=gitlab&logoColor=white)](https://gitlab.com/)

---

## 🎯 프로젝트 소개

이 저장소는 **AI MCP(Model Context Protocol) 플랫폼**을 처음부터 끝까지,
이론 개념부터 실전 배포까지 단계별로 정복하는 **전자책**입니다.

단순한 LLM API 호출을 넘어,  
**기업 환경에서 실제로 운영 가능한 AI Middleware 플랫폼**을 직접 설계하고 구축합니다.

### 이 책이 다루는 것
- ✅ MCP가 왜 필요한지, 기존 방식과 무엇이 다른지
- ✅ Gateway / Orchestrator / RAG / Tool / Policy / Audit 전체 구조
- ✅ FastAPI + Spring Boot 실습 코드 (복붙 가능)
- ✅ Windows 11 로컬 → Linux 서버 실전 배포
- ✅ Podman Gateway + Minikube Orchestrator 배포
- ✅ GitLab CI/CD + ArgoCD GitOps 파이프라인
- ✅ Zero Trust 보안 (mTLS / Istio / RBAC / DLP)
- ✅ Prompt 거버넌스, LLM 비용 최적화, Observability
- ✅ ERP 연동 End-to-End 실전 PoC 시나리오

---

## 👥 대상 독자

✅ MCP / AI Gateway 개념은 들었지만 구조가 잘 안 보이는 **주니어 개발자**  
✅ PoC 이후 어떻게 운영 시스템으로 가져가야 할지 모르는 **개발자/팀장**  
✅ 기업 내부 AI 시스템을 직접 구축해야 하는 **백엔드 / DevOps 엔지니어**  
✅ 보안 / 감사 / 정책까지 고려한 설계가 필요한 **시니어 / 아키텍트**

---

## 📖 커리큘럼

### 전체 목차

| Chapter | 제목 | 핵심 내용 |
|:---:|---|---|
| [0](./docs/chapter-00-intro.md) | 들어가며 — 왜 MCP인가 | 배경, LLM 한계, 이 책의 구성 |
| [1](./docs/chapter-01-concept.md) | MCP 개념과 아키텍처 | Middleware 정의, 조감도, 사례 |
| [2](./docs/chapter-02-functions.md) | MCP 핵심 기능 8가지 | 라우팅, Context, RAG, Tool, 보안, 감사, 캐시, 장애 |
| [3](./docs/chapter-03-api.md) | API 설계 & 인터페이스 | Chat/Context/RAG/Tool/Policy API |
| [4](./docs/chapter-04-msa.md) | MSA 구조 설계 | 서비스 경계, Mono-repo, 역할 |
| [5](./docs/chapter-05-env.md) | 실습 환경 구성 | Windows11 + Docker + Podman + Minikube + GitLab |
| [6](./docs/chapter-06-code.md) | 실습 — FastAPI로 구현하기 | Gateway, Orchestrator, Redis, RAG, Tool, Spring Boot |
| [7](./docs/chapter-07-infra.md) | 인프라 & 배포 | Docker Compose, Podman, Minikube, Helm, HPA |
| [8](./docs/chapter-08-cicd.md) | CI/CD 파이프라인 | GitLab CI, GitLab Actions, ArgoCD, Canary, Rollback |
| [9](./docs/chapter-09-security.md) | 보안 아키텍처 | DMZ, mTLS, Istio, Zero Trust, RBAC, SIEM |
| [10](./docs/chapter-10-dlp.md) | 보안 심화 — DLP & 이상탐지 | 민감정보 탐지, API Abuse, UEBA, 대응 흐름 |
| [11](./docs/chapter-11-prompt.md) | Prompt 거버넌스 | 버전관리, 품질 평가, Eval, 레지스트리 |
| [12](./docs/chapter-12-llm-ops.md) | LLM 운영 전략 | 모델 선택, 지능형 라우팅, 토큰 관리, Fallback |
| [13](./docs/chapter-13-observability.md) | Observability | Prometheus, Grafana, Alert 룰 |
| [14](./docs/chapter-14-ops.md) | 운영 설계 | DB 스키마, Redis TTL, DR, SLA/SLO, ROI |
| [15](./docs/chapter-15-poc.md) | 실전 PoC — ERP 연동 End-to-End | 시나리오, ERP Tool, 전체 연동, 검증, 트러블슈팅 |

---

## 🗺️ 학습 로드맵

### ⚡ 빠른 개념 파악 (1시간)
**MCP가 뭔지 빠르게 잡고 싶은 분**
1. Chapter 0: 들어가며
2. Chapter 1: MCP 개념과 아키텍처
3. Chapter 2: 핵심 기능 8가지

### 💻 개발자 트랙 (1일)
**코드로 직접 구현하고 싶은 분**
1. Chapter 0~4: 개념 + 설계
2. Chapter 5: 환경 구성
3. Chapter 6~7: 코드 구현 + 배포
4. Chapter 15: ERP PoC 직접 실행

### 🔐 보안/아키텍트 트랙 (반나절)
**보안 설계가 핵심인 분**
1. Chapter 1, 4: 구조 파악
2. Chapter 9: 보안 아키텍처
3. Chapter 10: DLP & 이상탐지
4. Chapter 14: 운영 설계

### 🚀 운영/DevOps 트랙 (반나절)
**배포 + 운영 파이프라인이 목적인 분**
1. Chapter 5: 환경 구성
2. Chapter 7: 인프라 & 배포
3. Chapter 8: CI/CD 파이프라인
4. Chapter 13: Observability
5. Chapter 14: 운영 설계

### 🎯 완전 정복 (3일)
**Chapter 0 → 15 순서대로 + 실습 직접 실행**

---

## 🛠️ 실습 환경

### 로컬 개발 환경
| 항목 | 스펙 |
|---|---|
| OS | Windows 11 |
| IDE | VSCode |
| Container | Docker Desktop |
| Gateway 배포 | Podman |

### 서버 환경
| 항목 | 스펙 |
|---|---|
| OS | Linux (Ubuntu 22.04 권장) |
| CI/CD | GitLab + GitLab Actions |
| Gateway | Podman 배포 |
| Orchestration | Minikube |

### 주요 기술 스택
| 영역 | 기술 |
|---|---|
| API Framework | FastAPI (메인) / Spring Boot (참고) |
| Cache | Redis |
| Database | PostgreSQL |
| Vector DB | PGVector |
| Service Mesh | Istio |
| GitOps | ArgoCD |
| Monitoring | Prometheus + Grafana |

---

## 📁 디렉토리 구조

```
zero-trust-ai-mcp/
├── README.md                        # 📄 이 파일
├── LICENSE                          # ⚖️ CC BY-NC-ND 4.0
│
├── docs/
│   ├── chapter-00-intro.md         # Chapter 0: 들어가며
│   ├── chapter-01-concept.md       # Chapter 1: MCP 개념과 아키텍처
│   ├── chapter-02-functions.md     # Chapter 2: 핵심 기능 8가지
│   ├── chapter-03-api.md           # Chapter 3: API 설계
│   ├── chapter-04-msa.md           # Chapter 4: MSA 구조 설계
│   ├── chapter-05-env.md           # Chapter 5: 실습 환경 구성
│   ├── chapter-06-code.md          # Chapter 6: FastAPI 구현
│   ├── chapter-07-infra.md         # Chapter 7: 인프라 & 배포
│   ├── chapter-08-cicd.md          # Chapter 8: CI/CD 파이프라인
│   ├── chapter-09-security.md      # Chapter 9: 보안 아키텍처
│   ├── chapter-10-dlp.md           # Chapter 10: DLP & 이상탐지
│   ├── chapter-11-prompt.md        # Chapter 11: Prompt 거버넌스
│   ├── chapter-12-llm-ops.md       # Chapter 12: LLM 운영 전략
│   ├── chapter-13-observability.md # Chapter 13: Observability
│   ├── chapter-14-ops.md           # Chapter 14: 운영 설계
│   └── chapter-15-poc.md           # Chapter 15: 실전 PoC
│
├── src/                             # 📦 실습 소스코드
│   ├── gateway/                    # FastAPI Gateway
│   ├── orchestrator/               # Orchestrator
│   ├── rag-service/                # RAG 검색
│   ├── tool-service/               # Tool (ERP 등)
│   ├── context-service/            # Context 관리
│   ├── policy-engine/              # 정책 엔진
│   └── audit-service/              # 감사 로그
│
├── infra/                           # ☸️ 인프라 설정
│   ├── helm/                       # Helm Charts
│   ├── k8s/                        # Kubernetes YAML
│   └── docker-compose.yml          # 로컬 전체 실행
│
└── assets/                          # 📊 다이어그램 이미지
    └── diagrams/
```

---

## 📜 라이선스

본 저작물은 **CC BY-NC-ND 4.0** 라이선스를 따릅니다.

### ✅ 허용 사항
- ✅ 개인 학습 목적 열람 및 다운로드
- ✅ 비영리 목적 공유 (출처 표시 필수)
- ✅ 스터디 그룹 등 비영리 교육 목적 사용

### ❌ 금지 사항
- ❌ 유료 강의 / 사내 교육 / 컨설팅 등 상업적 이용
- ❌ 내용 수정, 번역, 2차 저작물 제작
- ❌ 라이선스 조건 변경

### 💼 상업적 이용 문의
- **이메일**: j4angguiop@gmail.com
- **제목**: [라이선스 문의] 상업적 이용 문의

자세한 내용은 [LICENSE](./LICENSE) 파일 참고

---

## 👤 저작자 정보

- **이름**: 정상혁 (Sanghyuk Jung)
- **이메일**: j4angguiop@gmail.com
- **블로그**: https://j4zlap.tistory.com
- **GitHub**: https://github.com/rechard0609

### 📅 저작 정보
- **작성 시작**: 2024년 12월
- **작성 환경**: 개인 시간, 개인 장비, 개인 비용
- **저작권**: 모든 권리는 정상혁 개인에게 있음

---

## 🤝 기여 방법

### 오탈자 / 오류 제보
1. [GitHub Issues](https://github.com/rechard0609/zero-trust-ai-mcp/issues)에 등록
2. 또는 이메일: j4angguiop@gmail.com

### Pull Request 가이드
**허용되는 PR**:
- ✅ 오탈자 수정
- ✅ 기술적 오류 정정
- ✅ 링크 깨짐 수정

**허용되지 않는 PR**:
- ❌ 내용 추가 / 변경
- ❌ 구조 변경
- ❌ 번역

---

## 📞 문의

| 구분 | 연락처 |
|---|---|
| 일반 문의 | j4angguiop@gmail.com / 제목: [MCP Guide] 문의 내용 |
| 라이선스 문의 | j4angguiop@gmail.com / 제목: [라이선스 문의] 상업적 이용 문의 |
| 기술 질문 | GitHub Issues 또는 블로그 댓글 |

---

## 🎓 추천 학습 순서

```
1. Chapter 0 읽기 (10분)
   → 왜 MCP가 필요한지 배경 이해

2. Chapter 1~2 읽기 (30분)
   → MCP 전체 그림 + 핵심 기능 파악

3. Chapter 5 실습 (30분)
   → Windows 11 환경 세팅 완료

4. Chapter 3~4 읽기 (30분)
   → API 설계 + MSA 구조 이해

5. Chapter 6~7 실습 (2시간)
   → FastAPI 구현 + Podman/Minikube 배포

6. Chapter 8 실습 (1시간)
   → GitLab CI/CD 파이프라인 구성

7. Chapter 9~10 읽기 (1시간)
   → 보안 아키텍처 + DLP 설계

8. Chapter 11~14 읽기 (1시간)
   → Prompt 거버넌스 + 운영 설계

9. Chapter 15 실습 (1시간)
   → ERP 연동 End-to-End PoC 완주
```

---

## ⭐ 이 책이 도움이 되셨다면

⭐ GitHub Star를 눌러주세요!  
📢 블로그/SNS 공유도 환영합니다 (출처 표시 필수)

---

**© 2025. 12월 업데이트 정상혁 (Sanghyuk Jung). All Rights Reserved.**  
**Licensed under CC BY-NC-ND 4.0**

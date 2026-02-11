# trap-mafia-v4

실시간 추론 기반 웹 게임 프로젝트 (Monorepo).

Backend(FastAPI) + Frontend(Next.js) + Docker Compose 기반 개발 환경을 사용합니다.

---

## 📦 Project Structure

```
apps/
  backend/
  frontend/
ops/
  compose/
  env/
docs/
  adr/
  mvp/
  schema/
  dev/
```

- `apps/backend` — FastAPI 서버
- `apps/frontend` — Next.js 프론트엔드
- `ops/compose` — Docker Compose 설정
- `ops/env` — 환경 변수 파일
- `docs` — 설계 및 개발 문서

---

## 🚀 Quick Start

### 1️⃣ Host 모드 (기본 개발 모드)

인프라는 Docker로, 앱은 로컬 프로세스로 실행합니다.

```bash
make host-up
```

포함 작업:

- 의존성 설치 (uv / pnpm)
- postgres / redis 실행
- DB 마이그레이션
- backend 실행 (8000)
- frontend 실행

종료: `Ctrl+C`

---

### 2️⃣ Local 모드 (최종 검증용)

전체 스택을 한 번에 실행합니다.

```bash
make local-up
```

---

## 🔧 자주 사용하는 명령어

```bash
make host-up-only      # 인프라만 실행
make host-logs         # 인프라 로그
make host-be           # backend만 실행
make host-fe           # frontend만 실행

make local-infra-up    # local 인프라만 실행
make local-down        # local 인프라 종료
```

---

## 📄 Documentation

- 개발 서버 가이드: `docs/dev/dev-server.md`
- 아키텍처 결정 기록: `docs/adr`
- 게임 설계: `docs/mvp`
- 스키마 / 타입 시스템: `docs/schema`

---

## 🧠 Development Principles

- Monorepo 기반 단일 코드베이스
- 인프라는 Docker Compose로 통일
- 개발(Host)과 검증(Local) 모드 분리
- `Makefile`을 실행 표준 진입점으로 사용

---

## 🛠 Requirements

- Docker + Docker Compose
- uv
- pnpm
- Node.js (LTS)

---

## 🐳 Docker

Compose project name:

```
trap-mafia-v4
```

---

문제 발생 시:

- Docker 실행 여부 확인
- 포트(5432, 6379, 8000) 충돌 확인
- `ops/env` 환경 파일 존재 여부 확인

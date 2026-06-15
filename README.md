# trap-mafia

trap-mafia는 실시간 멀티플레이어 소셜 디덕션 게임입니다. 쉽게 말하자면 유사 마피아 웹게임입니다.
플레이어는 빨간 팀과 파란 팀 중 하나에 소속되지만 자신이 어떤 팀에 속하는지는 모르는 채로 게임을 진행하게 됩니다.

> **현재 상태:** v4 개발 임시 중단. 초기 버전들은 게임 설계상의 문제와 아키텍처 문제로 재시작 하였습니다.

---

## 🛠 Tech Stack

| 영역 | 기술 |
|------|------|
| Backend | FastAPI, Python, SQLAlchemy, PostgreSQL, Redis |
| Frontend | Next.js, TypeScript |
| 실시간 통신 | SSE (Server-Sent Events) |
| Infra | Docker Compose, Caddy |

### 실시간 통신 방식 선택: SSE

게임 이벤트(투표 결과, 역할 공개, 페이즈 전환 등)는 **서버 → 전체 참여자로의 단방향 브로드캐스트**로 충분합니다.
투표 등 클라이언트 → 서버 방향의 액션은 REST API로 처리할 수 있어 WebSocket과 같은 양방향 연결이 필요하지 않습니다.
SSE는 이 구조에 적합하며 구현 복잡도도 낮습니다.

이외의 주요 기술 선택의 배경은 [docs/adr](./docs/adr)에 기록되어 있습니다.

---

## 📦 Project Structure

```
apps/
  backend/        # FastAPI 서버
  frontend/       # Next.js 프론트엔드
ops/
  compose/        # Docker Compose 설정
  env/            # 환경 변수 파일
docs/
  adr/            # 아키텍처 결정 기록
  mvp/            # 게임 설계
  schema/         # 스키마 / 타입 시스템
  dev/            # 개발 서버 가이드
infra/
  edge/caddy/     # Caddy 리버스 프록시 설정
```

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

- 개발 서버 가이드: [docs/dev/dev-server.md](./docs/dev/dev-server.md)
- 아키텍처 결정 기록: [docs/adr](./docs/adr)
- 게임 설계: [docs/mvp](./docs/mvp)
- 스키마 / 타입 시스템: [docs/schema](./docs/schema)

---

## 🧠 Development Principles

- Monorepo 기반 단일 코드베이스
- 인프라는 Docker Compose로 통일
- 개발(Host)과 검증(Local) 모드 분리
- `Makefile`을 실행 표준 진입점으로 사용
- `pre-commit`으로 코드 품질 일관성 유지

---

## ✅ Requirements

- Docker + Docker Compose
- uv
- pnpm
- Node.js (LTS)

---

## 트러블슈팅

문제 발생 시 아래 항목을 확인하세요.

- Docker 실행 여부 확인
- 포트(5432, 6379, 8000) 충돌 확인
- `ops/env` 환경 파일 존재 여부 확인

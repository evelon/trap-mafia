# 개발 서버 가이드

이 프로젝트는 `Makefile`을 통해 두 가지 개발 모드를 제공합니다.

---

## 1. Host 모드 (기본 개발 모드)

**일상 개발 시 권장되는 모드입니다.**

- DB/Redis → Docker Compose로 실행
- Backend/Frontend → 로컬 프로세스로 실행

### 전체 실행

```bash
make host-up
```

다음이 자동으로 수행됩니다:

- 의존성 설치 (uv + pnpm)
- postgres / redis 실행 (compose host 설정)
- 마이그레이션 실행
- backend 실행 (port 8000)
- frontend 실행 (pnpm dev 기본 포트)

종료: `Ctrl+C`

### 인프라만 실행

```bash
make host-up-only
```

### 인프라 로그 확인

```bash
make host-logs
```

### 앱을 각각 실행

```bash
make host-be
make host-fe
```

---

## 2. Local 모드 (최종 검증용)

푸시/머지 전에 사용하는 검증 모드입니다.

인프라 + backend + frontend를 한 번에 실행합니다.

```bash
make local-up
```

다음이 수행됩니다:

- 의존성 설치
- compose (local 설정) 실행
- 마이그레이션 실행
- backend + frontend 동시 실행

종료: `Ctrl+C`

인프라만 실행:

```bash
make local-infra-up
```

---

## 환경 파일

### Compose 환경

- `ops/env/compose.host.env`
- `ops/env/compose.local.env`

### Runtime 환경 (Makefile이 자동 로드)

- `ops/env/runtime.host.env`
- `ops/env/runtime.local.env`

---

## 포트 정보

- Postgres: 5432
- Redis: 6379
- Backend: 8000
- Frontend: pnpm dev 기본 포트

---

## 참고 사항

- `*-only` 타겟은 의존성 설치 및 마이그레이션을 수행하지 않습니다.
- `make host-up`, `make local-up`은 deps + migrate를 포함합니다.
- Docker Compose 프로젝트 이름: `trap-mafia-v4`

문제가 발생하면 아래를 확인하세요:

- 포트 충돌 여부
- `ops/env` 경로에 환경 파일 존재 여부
- Docker 실행 상태

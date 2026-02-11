# ADR-0005: Development Workflow (Host / Local) via Makefile

## Status

Accepted

## Context

이 프로젝트는 단일 Monorepo + Docker Compose 베이스라인을 채택했다(ADR-0001).

개발 과정에서 다음 요구사항이 반복적으로 발생한다.

- DB(Postgres) / Cache(Redis)는 로컬/서버 환경에서 **일관되게 Docker Compose로** 기동하고 싶다.
- Backend/Frontend는 개발 속도(핫리로드, 디버깅 편의) 때문에 **로컬 프로세스로 실행**하는 흐름이 필요하다.
- 반면, 푸시/머지 전에는 “한 번에” 전체 스택을 기동하여 **최종 검증**할 수 있어야 한다.
- 환경 변수 파일이 여러 개로 분리되어 있어(Compose용 / Runtime용) 실수 없이 적용되도록 표준화가 필요하다.

또한 Makefile은 단순 명령 모음이 아니라, 팀원이 합류하거나 시간이 지난 후에도
"어떤 모드로 무엇을 어떻게 띄우는지"를 재현 가능한 형태로 제공해야 한다.

## Scope & Non-Goals

### Scope

- 개발/검증 환경에서의 **서비스 기동 표준**(Host / Local)
- 의존성 설치, 마이그레이션, 인프라 기동의 실행 순서 및 규칙
- Compose env와 Runtime env의 책임 분리 및 로딩 방식

### Non-Goals

- 배포(prod) 워크플로우 및 서버 배포 스크립트(별도 문서/ADR 범위)
- CI에서의 테스트/빌드 자동화(별도 문서/ADR 범위)
- 고가용성/멀티서버 구성(현 단계 목표 아님)

## Decision

`Makefile`을 개발 환경의 표준 진입점으로 두고, 다음 두 모드를 제공한다.

### 1) Host 모드 (기본 개발 모드)

- 인프라(Postgres/Redis)는 **Docker Compose(host 구성)**로 실행한다.
- Backend/Frontend는 **로컬 프로세스**로 실행한다.
- 목적: 빠른 반복 개발(핫리로드/디버깅), 인프라 구성의 재현성 확보.

대표 타겟:

- `make host-up`: deps + infra up + migrate + (backend+frontend 로컬 동시 실행)
- `make host-up-only`: infra up only (deps/migrate/app 실행 없음)
- `make host-logs`: 인프라 로그 tail

### 2) Local 모드 (최종 검증용)

- 인프라(Postgres/Redis)는 **Docker Compose(local 구성)**로 실행한다.
- Backend/Frontend는 **한 세션에서 동시 실행**(one-shot)한다.
- 목적: 푸시/머지 전 “한 번에” 기동하여 최종 검증.

대표 타겟:

- `make local-up`: deps + infra up + migrate + (backend+frontend 동시 실행)
- `make local-up-only`: deps 제외 + infra up + migrate + (backend+frontend 동시 실행)

### 3) `*-only` 규칙

기본 타겟은 편의성을 위해 deps/migration을 포함하고,
`*-only` 타겟은 **순수 실행만** 수행한다.

예:

- `host-migrate` vs `host-migrate-only`
- `host-up` vs `host-up-only`

### 4) 환경 변수 파일 분리 및 자동 로딩

- Compose env: `ops/env/compose.{host,local}.env`
- Runtime env: `ops/env/runtime.{host,local}.env` (Makefile이 자동 `source`)

Runtime env는 `host-be`, `host-fe`, `host-app-up`, `local-up` 등 앱 실행 시점에 자동 주입한다.

### 5) Compose project name 고정

Compose 리소스(네트워크/컨테이너/볼륨)의 안정성을 위해
`COMPOSE_PROJECT_NAME`을 `trap-mafia-v4`로 고정한다.

## Options Considered

### Option A: 모든 서비스를 Compose로만 실행

- 장점
  - 기동 방식이 단일화됨
  - 환경 재현성이 높음
- 단점
  - BE/FE 개발 시 핫리로드/디버깅 동선이 불편해질 수 있음
  - 로컬 도구(uv, pnpm) 기반 개발 흐름과 충돌 가능

### Option B: 인프라는 Compose, 앱은 로컬 실행 (Selected)

- 장점
  - 인프라는 재현성 있게 유지하면서, 앱 개발은 빠르게 반복 가능
  - 개발자 경험(핫리로드, IDE 디버깅)이 좋음
- 단점
  - “한 방에” 띄우기 요구가 남음

### Option C: Host/Local 모드로 분리하여 두 흐름을 모두 제공 (Selected)

- 장점
  - 개발(Host)과 최종 검증(Local)의 목적을 분리하여 각각 최적화
  - 팀 합류 시 실행 규칙이 명확해짐
- 단점
  - 타겟 수가 늘어나 관리가 필요

## Rationale

- 인프라는 Compose로 통일하여 DB/Redis 구성의 드리프트를 줄이고,
  단일 서버 운영(ADR-0001)과도 정합성을 유지한다.
- 앱은 로컬 실행을 기본으로 하여 개발 반복 속도와 디버깅 편의성을 확보한다.
- 푸시/머지 전에는 Local 모드로 전체를 한 번에 기동하여 최종 검증 흐름을 단순화한다.
- `*-only` 규칙으로 “빠른 실행”과 “편의 자동화”를 동시에 지원한다.
- env 파일을 Compose/Runtime으로 분리하고, Runtime env 자동 로딩을 제공하여
  실수(잘못된 env 적용/누락)를 줄인다.

## Consequences

### Positive

- 개발/검증 기동 방식이 표준화되어 온보딩 비용 감소
- 핫리로드/디버깅 편의 유지 + 인프라 재현성 확보
- deps/migrate 포함 여부를 `*-only`로 명확히 제어 가능

### Negative / Risks

- 모드/타겟이 늘어나 문서가 없으면 혼란 가능
- 로컬 프로세스와 Compose 로그가 분리되어 관찰성이 떨어질 수 있음

### Mitigations

- `docs/dev/dev-server.md`에 실전 가이드 제공
- `make help`를 최신 SSOT로 유지
- 필요 시 “통합 로그/프로세스 관리” 도구(concurrently/foreman/tmux 등) 도입을 재검토

## Rollout / Next Steps

- `Makefile` 타겟 및 `docs/dev/dev-server.md`를 최신 상태로 유지
- 마이그레이션/리셋 등 DB 관련 타겟을 `*-only` 규칙에 맞춰 단계적으로 확장
- CI/PR에서 local-up에 준하는 검증 흐름이 필요해지면 별도 ADR로 분리하여 결정

---

Last updated: 2026-02-12

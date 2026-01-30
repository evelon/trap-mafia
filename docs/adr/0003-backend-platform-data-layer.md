# ADR-0003: Backend Platform & Data Layer

## Status

Accepted

## Context

이 프로젝트는 웹 기반 게임 서비스로,  
**SSE(Server-Sent Events) 및 WebSocket을 통한 실시간 상태 전달**을 핵심 요구사항으로 가진다.

초기 단계의 제약 및 전제는 다음과 같다.

- 동시 접속 목표는 약 20–100명 수준
- 단일 서버에서 BE를 운영하며, 추후 점진적 분리를 고려
- 게임의 핵심 상태는 유실되면 안 됨
  - room_id
  - 참여 플레이어
  - 플레이어의 팀
  - 투표 내역 및 결과
  - 현재 round / phase
- 실시간 연결(SSE/WS)과 DB 접근이 동시에 발생할 수 있음

이 단계에서 해결하려는 핵심 문제는 다음과 같다.

- 실시간 연결과 궁합이 좋은 Backend 프레임워크 선택
- 유실되면 안 되는 상태를 안전하게 저장할 데이터 계층 결정
- 초기 구현 복잡도를 과도하게 높이지 않으면서 확장 가능성 확보

## Scope & Non-Goals

- 이 ADR은 **Backend 플랫폼 및 데이터 계층 선택**만을 다룬다.
- 게임 도메인 모델의 상세 설계는 다루지 않는다.
- 성능 튜닝, 대규모 확장, 고가용성 구성은 현 단계의 목표가 아니다.

## Decision

다음과 같은 Backend 및 데이터 계층 구성을 채택한다.

- Backend Framework: **FastAPI**
- DB Access Pattern: **Async-first (AsyncEngine / AsyncSession)**
- Database: **Postgres**
- Cache / Coordination: **Redis**
- ORM & Migration: **SQLAlchemy + Alembic**

## Options Considered

### Option A: Django + Sync ORM

- 장점
  - 풍부한 기능과 레퍼런스
  - 안정적인 생태계
- 단점
  - 실시간 통신(SSE/WS) 구현 시 구조가 복잡해짐
  - async 사용 시 학습 비용 및 제약이 큼
  - 이 프로젝트에 불필요한 기능이 많음

### Option B: FastAPI + Async Stack (Selected)

- 장점
  - 기본 구조가 단순하고 레이어가 얇음
  - SSE/WS 엔드포인트를 직접 구현하기 쉬움
  - async 기반으로 실시간 연결 모델과 자연스럽게 결합
- 단점
  - Django 대비 제공 기능이 적음
  - 일부 기능은 직접 구현 필요

## Rationale

### Backend Framework

이 프로젝트는 **SSE 및 WebSocket을 중심으로 한 실시간 상태 전달**이 핵심이다.  
하지만 이러한 요구사항을 "프레임워크가 대신 해결해 주는" 생태계는 사실상 존재하지 않는다.

따라서, 사용해 본 프레임워크 중에서  
**기본 구조가 단순하고, 실시간 엔드포인트를 직접 구현하기 가장 편한** FastAPI를 선택한다.

### Async-first 접근

여러 클라이언트와의 SSE 연결을 장시간 유지하면서  
동시에 DB 및 Redis 접근이 발생할 수 있으므로,  
**async 기반 실행 모델로 통일**하여 구현 일관성을 유지한다.

sync 방식으로도 구현은 가능하지만,  
초기 설계 단계에서 sync/async를 혼용하면 세션 관리와 실행 모델이 복잡해질 수 있으므로  
단일 패턴(async)을 채택한다.

### Database

게임의 핵심 상태는 유실되면 안 되므로,  
**RDBMS를 SSOT(Single Source of Truth)**로 사용한다.

MariaDB/MySQL과 비교했을 때,  
Postgres가 제공하는 기능과 확장성이 더 넓다고 판단하여 Postgres를 선택한다.

### Redis

초기에는 단일 서버로 운영하지만,  
워커 확장 시 **프로세스 간 상태 공유 및 이벤트 전달**이 필요해진다.

이를 위해 Redis를 사용하며,  
PubSub을 통해 실시간 이벤트 fan-out 구조(SSE 확장)를 대비한다.

### ORM & Migration

FastAPI 환경에서 SQLAlchemy는 사실상 표준 ORM이며,  
Alembic은 이에 대응하는 표준 마이그레이션 도구다.

마이그레이션은 **Alembic autogenerate를 기본**으로 사용하며,  
필요 시 리뷰 후 수동 조정을 옵션으로 둔다.

## Consequences

### Positive

- 실시간 통신(SSE/WS)에 적합한 Backend 구조
- 실행 모델(async)과 요구사항 간 일관성 확보
- 표준적이고 검증된 ORM / Migration 도구 사용
- 추후 워커 확장 시 Redis 기반 구조로 자연스러운 확장 가능

### Negative / Risks

- async 기반 구현에 대한 학습 비용
- 프레임워크가 제공하지 않는 기능은 직접 구현 필요

### Mitigations

- 초기에는 단순한 도메인 모델로 시작하여 복잡도 관리
- ADR 및 코드 구조를 통해 async 사용 규칙을 명확히 문서화
- 요구사항 변화 시 sync/async 전략 재검토 가능성 유지

## Rollout / Next Steps

- Backend async 스캐폴딩 확정
- 핵심 도메인 모델(Room, Player, Vote 등) 설계
- SSE 엔드포인트 기본 구조 구현
- Frontend와의 실시간 상태 연동 테스트

---

Last updated: 2026-01-29

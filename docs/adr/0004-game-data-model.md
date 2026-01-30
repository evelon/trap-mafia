# ADR-0004: Game Data Model (Cases / Phases / Votes)

## Status

Accepted

## Context

이 프로젝트는 웹 기반 추론 게임 서비스로,  
**SSE(Server-Sent Events) 및 WebSocket을 통한 실시간 상태 전달**을 핵심 요구사항으로 가진다.

Backend는 FastAPI 기반 async 구조이며,  
게임의 모든 핵심 상태는 **RDBMS(Postgres)를 SSOT(Single Source of Truth)**로 관리한다  
(ADR-0003 참조).

유실되면 안 되는 상태는 다음과 같다.

- 게임의 현재 진행 상태 (round / phase)
- 참여 플레이어 및 좌석 정보
- 플레이어의 팀 정보 (서버 전용)
- 투표 내역 (누가 누구에게 투표했는지)
- 투표 결과에 따라 누적되는 플레이어 상태 변화
- DISCUSS phase에서의 준비(ready) 상태

클라이언트는 서버가 전달하는 **상태 스냅샷(snapshot)**을 기준으로 화면을 갱신하며,  
서버는 모든 상태 조립과 검증을 담당한다.

게임 룰은 아직 고정되지 않았으며, 특히 다음 요소는 변경 가능성을 가진다.

- 플레이어 life 수 (1, 2, 3 이상)
- phase 구성 및 순서
- 투표 제한 규칙
- NIGHT 및 VOTE phase의 제한 시간
- DISCUSS phase의 종료 조건

따라서 데이터 모델은 **정확성, 단순성, 룰 변경 내성**을 동시에 만족해야 한다.

---

## Scope & Non-Goals

### Scope

- 게임 세션 단위의 데이터 모델 정의
- 플레이어, phase, 투표에 대한 영속 구조
- DISCUSS phase의 조건 기반 종료를 위한 상태 모델링
- Backend가 snapshot을 조립하기 위한 최소 정규화

### Non-Goals

- Event Sourcing 전면 도입
- 상태 변화 단위의 이벤트 로그 테이블
- 클라이언트 UI 전용 상태 저장
- 채팅, 로그, 통계용 데이터 모델
- 고급 분석/완전 리플레이 전용 구조

---

## Event Sourcing에 대한 정의 및 범위

이 문서에서 말하는 *Event Sourcing*이란:

- 모든 상태 변화를 불변 이벤트로 기록
- 현재 상태는 이벤트 로그를 순차 적용하여 재구성
- 이벤트 로그 자체가 SSOT가 되는 모델

Event Sourcing은 강력한 감사(audit) 및 완전 리플레이를 가능하게 하지만,  
초기 구현 복잡도와 운영 비용이 높다.

본 프로젝트는 현재 단계에서:

- 소규모 동시 접속
- 단일 서버 기반 운영
- 빠른 룰 실험과 반복 개발

을 우선시하므로, **Event Sourcing을 채택하지 않는다**.

다만 Phase / Vote / Ready 구조를 통해  
**필요 시 이벤트 기반 구조로 확장 가능한 여지**는 유지한다.

---

## Decision

다음과 같은 **Case 단위 정규 데이터 모델**을 채택한다.

### 핵심 원칙

- 하나의 `case`는 하나의 게임 세션을 의미한다
- 모든 핵심 상태는 DB에 저장되며, 서버가 SSOT이다
- 클라이언트에는 상태의 “결과와 의미”만 전달한다
- 룰 변경 가능성이 높은 요소는 수치 기반 또는 조건 기반으로 저장한다
- 시간 제한과 종료 조건은 상태와 분리하여 설정/입력으로 관리한다

---

## Data Model Overview

### 주요 테이블

- `cases`: 게임 세션 및 현재 진행 상태
- `case_settings`: 게임 시작 시 고정되는 규칙
- `case_players`: 게임 참가자 및 누적 상태
- `phases`: 게임 진행 단계 (round + 순서)
- `votes`: 투표 원본 입력 로그
- `phase_readies`: DISCUSS phase 종료를 위한 준비 상태 기록

---

## Key Design Decisions

### 1. Phase 단위 상태 모델링

- 게임 진행은 `phase` 단위로 분해한다
- `round_no`와 `seq_in_round`를 통해 명확한 순서를 표현한다
- `phase_type`은 `NIGHT / DISCUSS / VOTE`로 정의한다
- `state (OPEN / CLOSED / RESOLVED)`를 통해
  - 입력 허용
  - 입력 종료
  - 결과 적용 완료
    를 명확히 구분한다

이를 통해:

- 멱등 처리
- 재접속 시 상태 복구
- SSE snapshot 조립

을 단순화한다.

---

### 2. Vote는 원본 입력 로그로 저장

- 투표는 유실되면 안 되는 핵심 입력이다
- `votes` 테이블은 입력 그대로를 저장한다
- 한 phase에서 한 플레이어는 한 번만 투표 가능하다
- 투표 변경은 FE에서만 허용하며,
  서버는 **첫 입력만 인정**하도록 제약한다

---

### 3. Life 상태는 수치 기반으로 저장

룰 변경 가능성을 고려하여:

- 플레이어 상태를 enum으로 고정하지 않는다
- 대신:
  - `life_lost` (누적 손실)
  - `full_life` (게임 설정)
    을 저장한다

현재 상태(탈락 여부 등)는
Backend에서 계산하여 snapshot에 포함한다.

---

### 4. Snapshot 중심의 상태 동기화

- Backend는 상태 변경 시마다 **전체 snapshot**을 생성한다
- Snapshot은 SSE를 통해 클라이언트에 전달된다
- Redis는 워커 확장 시 fan-out/coordination 용도로만 사용한다
- DB는 항상 최종 상태의 SSOT로 유지된다

이 구조는 ADR-0003의 Backend 설계와 일관된다.

---

### 5. Phase Time Limit 모델링 (NIGHT / VOTE)

- NIGHT 및 VOTE phase는 제한 시간을 가진다
- 제한 시간은 게임 규칙에 해당하므로, **case_settings**에 정의한다
- phase에는 실제 발생한 시각만 기록한다
  - `opened_at`: phase 시작 시각
  - `closed_at`: 입력 종료 시각
  - `resolved_at`: 결과 적용 완료 시각

Backend는 phase 시작 시:

- `opened_at`을 기록하고
- 설정된 제한 시간을 기준으로 종료 시점을 계산하여
- 타이머 또는 background task를 통해 phase를 종료한다

---

### 6. DISCUSS Phase의 조건 기반 종료 모델링

- DISCUSS phase는 시간 만료가 아닌 **조건 충족 시 종료**된다
- 종료 조건은 **해당 phase에 참여 중인 모든 유효 플레이어가 ready 상태가 되는 것**이다
- 각 플레이어의 ready 입력은 `phase_readies` 테이블에 저장한다
- ready 상태는 phase 전이를 위한 핵심 입력이므로 **DB에 영속화**한다

Backend는 DISCUSS phase에서:

- 탈락하지 않은 플레이어 수와
- 해당 phase에 대한 ready 기록 수를 비교하여
- 종료 조건 충족 시 phase를 종료하고 다음 phase로 전이한다

필요한 경우를 대비하여:

- `discuss_duration_sec` 설정을 통해
  최대 대기 시간을 둘 수 있으며,
  값이 0인 경우 무제한으로 해석한다

이로써 DISCUSS phase의 **조건 기반 종료**와  
NIGHT / VOTE phase의 **시간 기반 종료**를
동일한 phase 모델 안에서 일관되게 표현한다.

---

## Options Considered

### Option A: Event Sourcing 기반 모델

- 장점
  - 완전한 상태 재생 가능
  - 감사 및 분석에 유리
- 단점
  - 초기 구현 및 운영 복잡도 증가
  - 현재 요구사항 대비 과설계

### Option B: Case + Phase + Vote + Ready 정규 모델 (선택)

- 장점
  - 단순하고 명확한 상태 관리
  - 시간 기반 / 조건 기반 종료를 모두 표현 가능
  - 룰 변경에 대한 내성
  - SSE snapshot 조립 용이
- 단점
  - 완전 리플레이는 추가 설계 필요

---

## Consequences

### Positive

- 서버 상태 관리 단순화
- Backend async 구조와의 정합성 확보
- 다양한 종료 조건을 일관된 모델로 표현
- 재접속 및 디버깅 용이

### Negative / Risks

- DISCUSS phase가 사용자 입력에 의존하므로
  일부 플레이어 미응답 시 지연 가능성 존재

### Mitigations

- `discuss_duration_sec`를 통한 최대 대기 시간 설정
- 필요 시 호스트 강제 진행 기능 추가 가능

---

## Rollout / Next Steps

- 본 ADR을 기준으로 데이터 모델 확정
- SQLAlchemy Async 모델 구현
- Alembic 초기 마이그레이션 생성
- Phase 전이 로직 및 타이머/ready 처리 구현
- Snapshot 조립 로직 및 SSE 연동 구현

---

Last updated: 2026-01-30

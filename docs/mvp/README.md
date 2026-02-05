# Trap MVP Scope

이 문서는 **Trap 게임의 MVP(최소 기능 제품)** 구현 범위를 명확히 정의하기 위한 문서이다.

본 문서는 `docs/schema/*`에 정의된 **최종 설계 문서의 축약본이 아니며**,
"지금 당장 구현할 것 / 구현하지 않을 것"을 명시적으로 선언하는 것을 목표로 한다.

---

## 1. MVP 목표

- 플레이어 4~8명이 **게임 1판을 끝까지 플레이 가능**
- 단일 room
- 단일 RUNNING case
- 서버 SSOT 기반 상태 관리
- SSE를 통한 실시간 상태 전파

---

## 2. MVP에서 구현하는 기능

### 게임 흐름

- room 생성 및 입장
- host에 의한 게임 시작
- NIGHT / DISCUSS / VOTE phase 진행
- red vote / blue vote 처리
- life 감소 및 게임 종료 판정

---

## 3. MVP DB Scope

### 사용 테이블

- users
- rooms
- room_members
- cases
- case_settings
- case_players
- phases
- red_votes
- blue_votes
- vote_results

### 미구현 / Stub 처리

- phase_readies (DISCUSS는 timeout 혹은 수동 skip 처리)
- case_history (DB 저장 없음, SSE로만 snapshot 전달)
- case_action_history (action log / receipt 미구현)

> 위 테이블들은 **최종 설계에는 존재하나**, MVP 단계에서는 구현하지 않는다.

---

## 4. MVP Rule Simplifications

- reconnect 시 과거 history 복구 없음
- snapshot은 메모리 기반으로만 생성
- idempotency_key 미적용
- 동일 phase 내 입력은 서버에서 1회만 허용
- INTERRUPTED 상태 미지원
- schema_version 고정 = 1
- room settings(=case settings)의 많은 부분 이용하지 않음

---

## 5. MVP API Scope

### REST API

- POST /api/rooms/current/start
- POST /api/phases/current/red-vote
- POST /api/phases/current/blue-vote
- POST /api/phases/current/discuss-skip

### SSE

- GET /rt/sse/case_snapshot

---

## 6. 입력 규칙 (MVP)

- 모든 플레이어 식별은 `seat_no` 기준
- red vote 요청: `{ "target_seat_no": number }`
- blue vote 요청: `{ "choice": "YES" | "NO" | "SKIP" }`
- targeter의 YES는 자동 처리되며 별도의 입력 없음

---

## 7. MVP에서 제외된 기능 (Post-MVP)

- case_history 영속 저장
- action_history 및 receipt
- SSE reconnect 시 증분 history 동기화
- multi-room
- spectator / peek
- game interrupt / resume

---

## 8. 문서 관계

- 본 문서는 **구현 범위 선언서**이다.
- 최종 스키마 및 규칙은 `docs/schema/README.md`를 기준으로 한다.
- MVP 이후 기능 확장은 본 문서를 수정하지 않고, schema 문서를 기준으로 진행한다.

---

## 9. 변경 정책

- MVP 범위 변경 시 이 문서를 먼저 수정한다.
- "안 만든 것"과 "아직 안 만든 것"을 구분하기 위해, 모든 제외 사항은 명시적으로 기록한다.

---

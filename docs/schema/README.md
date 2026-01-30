# Database Schema (DBML)

이 디렉토리는 게임 서버의 **논리적 데이터 모델(schema)** 을 DBML 형식으로 관리한다.  
여기에 정의된 스키마는 **게임 도메인의 기준(Source of Truth)** 이며,  
구현 코드(SQLAlchemy, Alembic)는 이 스키마와 ADR을 참고하여 **수동으로 작성**한다.

---

## 파일 구성

### `game.dbml`

게임 한 판(case)을 중심으로 한 전체 데이터 모델 정의이다.

포함되는 주요 도메인은 다음과 같다.

- 게임 세션 (`cases`)
- 게임 규칙 (`case_settings`)
- 게임 참가자 (`case_players`)
- 게임 진행 단계 (`phases`)
- 투표 입력 (`votes`)
- DISCUSS 단계의 준비 상태 (`phase_readies`)

이 파일은 **실행 코드가 아닌 설계 문서**이며,  
자동 마이그레이션이나 코드 생성의 입력으로 사용하지 않는다.

---

## 설계 원칙

### 1. Server-Side SSOT

- 게임의 모든 핵심 상태는 DB에 저장된다.
- 서버가 단일한 상태 결정자(Single Source of Truth)이다.
- 클라이언트는 서버가 조립한 snapshot만을 기준으로 동작한다.

### 2. Case = 하나의 게임 세션

- `cases` 테이블의 한 row는 **한 번의 게임 플레이**를 의미한다.
- 재접속, 서버 재시작 이후에도 게임 상태를 복원할 수 있어야 한다.

### 3. Phase 중심 상태 모델

- 게임 진행은 `phases` 단위로 표현된다.
- `round_no` + `seq_in_round` 조합으로 진행 순서를 명확히 한다.
- `phase_type`:
  - `NIGHT`
  - `DISCUSS`
  - `VOTE`
- `phase_state`:
  - `OPEN` : 입력 가능
  - `CLOSED` : 입력 종료
  - `RESOLVED` : 결과 적용 완료

---

## 시간 기반 / 조건 기반 Phase 종료

### NIGHT / VOTE

- 시간 제한을 가진 phase이다.
- 제한 시간은 **규칙(rule)** 이므로 `case_settings`에 정의한다.
  - `night_duration_sec`
  - `vote_duration_sec`
- `phases` 테이블에는 실제 발생 시각만 기록한다.
  - `opened_at`
  - `closed_at`
  - `resolved_at`

### DISCUSS

- 시간 만료가 아닌 **조건 기반 종료**를 가진 phase이다.
- 모든 유효 플레이어가 ready 상태가 되면 종료된다.
- 각 플레이어의 ready 입력은 `phase_readies` 테이블에 저장된다.
- 필요 시 `discuss_duration_sec`를 통해 최대 대기 시간을 둘 수 있다.
  - `0`은 무제한을 의미한다.

---

## Life 모델링

- 플레이어의 생존 상태는 enum으로 고정하지 않는다.
- 대신 수치 기반 모델을 사용한다.
  - `case_settings.full_life`
  - `case_players.life_lost`
- 현재 상태(탈락 여부 등)는 서버 로직에서 계산하여 snapshot에 포함한다.

이 방식은:

- 게임 룰 변경(목숨 1/2/3 이상)에 유연하고
- DB 마이그레이션 비용을 줄인다.

---

## Vote 모델링

- `votes` 테이블은 **원본 입력 로그**이다.
- 한 phase에서 한 플레이어는 한 번만 투표 가능하다.
- `(phase_id, voter_player_id)` 유니크 제약을 통해 서버에서 이를 강제한다.
- 투표 변경은 FE에서만 허용하며, 서버는 첫 입력만 인정한다.

---

## 변경 관리 규칙

- 스키마의 **의미가 바뀌는 변경**이 있을 경우:
  1. 관련 ADR을 먼저 수정한다.
  2. `game.dbml`을 수정하여 설계를 반영한다.
  3. 이후 구현 코드(SQLAlchemy / Alembic)를 수정한다.

- 단순한 인덱스 추가, 주석 보강 등
  **의미를 바꾸지 않는 변경**은 ADR 없이 허용한다.

---

## 참고 문서

- ADR-0003: Backend Architecture
- ADR-0004: Game Data Model

이 디렉토리는  
“왜 이런 선택을 했는가”보다는  
“현재 데이터 모델이 무엇인가”를 명확히 하기 위한 용도이다.

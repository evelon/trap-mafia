# Database Schema (DBML)

이 디렉토리는 게임 서버의 **논리적 데이터 모델(schema)** 을 DBML 형식으로 관리한다.  
여기에 정의된 스키마는 **게임 도메인의 기준(Source of Truth)** 이며,  
구현 코드(SQLAlchemy, Alembic)는 이 스키마와 ADR을 참고하여 **수동으로 작성**한다.

---

## 파일 구성

### `game.dbml`

게임 한 판(case)을 중심으로 한 전체 데이터 모델 정의이다.

포함되는 주요 도메인은 다음과 같다.

- 사용자 (`users`)
- 룸/로비 (`rooms`, `room_members`, `room_settings`)
- 게임 세션 (`cases`)
- 게임 규칙 (`case_settings`)
- 게임 참가자 및 상태/자원 (`case_players` — `life_lost`, `vote_tokens`)
- 게임 진행 단계 (`phases`)
- VOTE 단계 메타(개시자/대상) (`phase_vote_meta`)
- 암전(RED) 투표 입력 (`red_votes`)
- 점등(BLUE) 투표 입력 (`blue_votes`)
- 투표 결과 (`vote_results`)
- DISCUSS 단계의 준비 상태 (`phase_readies`)

이 파일은 **실행 코드가 아닌 설계 문서**이며,  
automatic migration이나 코드 생성의 입력으로 사용하지 않는다.

---

## 설계 원칙

### 1. Server-Side SSOT

- 게임의 모든 핵심 상태는 DB에 저장된다.
- 서버가 단일한 상태 결정자(Single Source of Truth)이다.
- 클라이언트는 서버가 조립한 snapshot만을 기준으로 동작한다.

### Case = 하나의 게임 플레이 기록

- `case`는 **한 번의 게임 플레이(한 판)** 를 의미한다.
- 사용자는 먼저 `room`에 입장하고,
  게임 시작 시점에 새로운 `case`가 생성된다.
- 하나의 `room`은 시간 흐름에 따라 여러 개의 `case`를 가질 수 있다.
- `case`는 게임 진행 상태와 결과를 영속화하기 위한 단위이다.

### Room 개념

- `room`은 게임이 시작되기 전과 후를 아우르는 **로비/컨테이너 개념**이다.
- 사용자는 `room`에 입장한 상태(`room_members`)에서
  게임 시작을 기다리거나, 다음 게임을 준비한다.
- 게임이 시작되면 해당 `room`에 새로운 `case`가 생성된다.
- 현재 개발 단계에서는 room 관련 동작을 단순화(예: 단일 room)하여 진행할 수 있으나,
  데이터 모델은 장기적으로 **1:N 구조(room:cases)** 확장을 전제로 설계되어 있다.

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
- 한 round(DAY) 내에서 생성 가능한 `VOTE` phase의 최대 횟수 역시 규칙에 포함된다.
  - `max_vote_phases_per_round`
  - 이는 "투표 입력 횟수"가 아니라, **phase 구성 제한**을 의미한다.
- `phases` 테이블에는 실제 발생 시각만 기록한다.
  - `opened_at`
  - `closed_at`
  - `resolved_at`

### DISCUSS

- DISCUSS는 조건 기반 종료(전원 ready)와 시간 기반 종료(타임아웃)를 모두 가진 phase이다.
- 전원이 ready가 되면 즉시 종료된다.
- `discuss_duration_sec`가 0이 아니면 최대 대기 시간이 적용되며, 타임아웃 시에도 종료된다.
- 각 플레이어의 ready 입력은 `phase_readies` 테이블에 저장된다.

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

## Token(표) 모델링

- 플레이어가 보유한 표의 개수는 `case_players.vote_tokens`로 저장한다.
- 표는 여러 개를 보유할 수 있으며, 투표에 참여할 때 보유한 표를 모두 소모하는 규칙을 서버 로직으로 적용한다.
- 표의 공개/비공개 여부는 DB가 아니라 snapshot 조립 단계에서 제어한다.
  - 투표 phase(`NIGHT`/`VOTE`) 진행 중에는 표 개수를 숨길 수 있다.

---

## Vote 모델링

- 투표 입력은 phase 성격에 따라 테이블을 분리한다.
  - `red_votes`: `phase_type=NIGHT`에서의 지목 투표 입력(암전/RED 투표)
  - `blue_votes`: `phase_type=VOTE`에서의 찬반 투표 입력(점등/BLUE 투표)
- 한 phase에서 한 플레이어는 한 번만 입력 가능하다.
  - `(phase_id, voter_player_id)` 유니크 제약을 통해 이를 강제한다.
  - 투표 변경은 FE에서만 허용하며, 서버는 첫 입력만 인정한다.

### VOTE 단계의 개시자/대상

- 점등 투표(`phase_type=VOTE`)는 DISCUSS 단계에서 한 플레이어가 대상을 지목하여 개시된다.
- 개시자/대상 정보는 투표 입력과 분리하여 `phase_vote_meta`에 저장한다.
  - `targeter_player_id`: 개시자
  - `targeted_player_id`: 투표 대상자

### 투표 결과

- 투표의 결과(표적 선정 여부)는 `vote_results`에 저장한다.
  - `targeted_player_id`가 `null`이면 표적 미선정
  - `fail_reason`는 표적이 선정되지 않은 경우의 사유를 기록한다. (예: `TIE`, `NO_VALID_VOTES`, `SINGLE_PARTICIPANT`)

투표 횟수 제한은 입력 테이블 수준에서 관리하지 않는다.
대신, 한 round(DAY)에서 생성 가능한 `VOTE` phase의 수를 제한하는 방식으로 모델링한다.
이 제한은 `case_settings.max_vote_phases_per_round`에 정의된다.

---

## 변경 관리 규칙

- 스키마의 **의미가 바뀌는 변경**이 있을 경우:
  1. 관련 ADR을 먼저 수정한다. (예: vote 규칙 변경, phase 구성 규칙 변경 등)
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

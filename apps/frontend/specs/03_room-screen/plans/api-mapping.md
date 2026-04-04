# API 매핑: 방 화면 UI (Room Screen)

## FR-001~003 / FR-004: 방 상태 실시간 수신 (방 이름·참가자·설정)

SSE로 수신한 `RoomSnapshot`에서 방 이름(`room.room_name`), 참가자 목록(`members`), 방 설정(`settings`)을 모두 추출한다. 별도 REST 조회 없이 SSE 최신 스냅샷을 단일 소스로 사용한다.

**SSE**

| 함수명 | 경로 | 응답 타입 | 비고 |
| ------ | ---- | --------- | ---- |
| `roomStateSseRtV1SseRoomsCurrentStateGet` | `GET /rt/v1/sse/rooms/current/state` | `EnvelopeRoomSnapshotSseEnvelopeCode` | fetch 기반, Axios 인터셉터 미적용. `data: RoomSnapshot \| null` |

**스냅샷 구조** (`RoomSnapshot`):

| 필드 | 타입 | 용도 |
| ---- | ---- | ---- |
| `room` | `RoomInfo` | 방 이름(`room_name`), 방장 ID(`host_user_id`) |
| `members` | `Array<RoomMember>` | 참가자 목록. 서버 정렬: `joined_at ASC` — 클라이언트 재정렬 불필요 |
| `settings` | `RoomSettings` | 방 설정 7개 필드 (`max_players`, `team_policy`, `full_life`, `max_vote_phases_per_round`, `night_duration_sec`, `vote_duration_sec`, `discuss_duration_sec`) |
| `current_case` | `RoomCaseInfo \| null` | 게임 진행 여부 판단 (null이면 대기 중, 값 있으면 진행 중) |
| `last_event` | `RoomSnapshotType \| null` | 이 스냅샷을 트리거한 이벤트 종류 |

**이벤트 타입** (`RoomSnapshotType`):

| 값 | UI 반응 |
| -- | ------- |
| `room.connected` | 초기 스냅샷 로드 완료 |
| `room.member.joined` | 참가자 추가 (스냅샷 전체 교체) |
| `room.member.left` | 참가자 제거 (스냅샷 전체 교체) |
| `room.case.started` | 게임 화면으로 이동 트리거 |

**SSE 스트림 종료**

| 함수명 | 경로 | 비고 |
| ------ | ---- | ---- |
| `closeRoomStateStreamRtV1SseRoomsCurrentClosePost` | `POST /rt/v1/sse/rooms/current/close` | 방 나가기 직전 또는 컴포넌트 언마운트 시 호출 |

---

## FR-005: 게임 시작

**REST API**

| 훅/함수 | 요청 타입 | 응답 타입 | 비고 |
| ------- | --------- | --------- | ---- |
| `caseStartApiV1RoomsCurrentCaseStartPostMutation` | `{ body: CaseStartRequest }` (`red_player_count: number \| null`) | `CaseStartResponse` | MVP에서 `red_player_count: null` 전달. 화면 이동 트리거는 REST 응답이 아니라 SSE `room.case.started` 이벤트 |

---

## FR-006: 게임 진행 중 상태 표시

**매핑 불가 (클라이언트 전용)**

| 사유 |
| ---- |
| SSE 스냅샷의 `current_case !== null` 조건으로 판단. 별도 API 호출 없음 |

---

## FR-007: 방 나가기

**REST API**

| 훅/함수 | 요청 타입 | 응답 타입 | 비고 |
| ------- | --------- | --------- | ---- |
| `leaveRoomApiV1RoomsCurrentLeavePostMutation` | 없음 | `LeaveRoomResponse` | 성공 시 SSE 스트림 종료 후 `/rooms`로 이동 |

---

## FR-008: 실시간 연결 오류 상태 표시

**매핑 불가 (클라이언트 전용)**

| 사유 |
| ---- |
| SSE `onSseError` 콜백 + `sseMaxRetryAttempts` 초과 시 클라이언트에서 오류 상태 관리. 별도 API 없음 |

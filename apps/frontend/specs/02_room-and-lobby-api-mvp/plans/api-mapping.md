# API 매핑: 방/로비 API 연동 및 라우팅 (MVP)

## FR-001 / FR-002: 방 참가 및 성공 시 화면 이동

**REST API**

| 훅/함수 | 요청 타입 | 응답 타입 | 비고 |
| ------- | --------- | --------- | ---- |
| `joinRoomApiV1RoomsRoomIdJoinPostMutation` | `JoinRoomApiV1RoomsRoomIdJoinPostData` (`path.room_id: string`) | `JoinRoomResponse` (`data: JoinRoomMutation \| null`) | MVP에서는 방 ID 하드코딩. `reason: 'JOINED' \| 'ALREADY_JOINED'` — 둘 다 성공으로 처리 가능 |

## FR-003 / FR-004: 실시간 방 상태 구독 (SSE) 및 자동 재연결

**SSE**

| 함수명 | 경로 | 응답 이벤트 타입 | 비고 |
| ------ | ---- | --------------- | ---- |
| `roomStateSseRtV1SseRoomsCurrentStateGet` | `GET /rt/v1/sse/rooms/current/state` | `RoomSnapshot` (event: `room_state`) | fetch 기반, Axios 인터셉터 미적용. `onSseEvent`, `onSseError` 콜백으로 처리. `sseDefaultRetryDelay: 3000`, `sseMaxRetryDelay: 30000`, `sseMaxRetryAttempts` 옵션 제공 |

**관련 REST (스트림 종료)**

| 훅/함수 | 요청 타입 | 응답 타입 | 비고 |
| ------- | --------- | --------- | ---- |
| `closeRoomStateStreamRtV1SseRoomsCurrentClosePostMutation` | 없음 | `EnvelopeRoomSnapshotSseEnvelopeCode` | 컴포넌트 언마운트 시 SSE 연결 종료 요청 |

## FR-005: 방 자발적 퇴장

**REST API**

| 훅/함수 | 요청 타입 | 응답 타입 | 비고 |
| ------- | --------- | --------- | ---- |
| `leaveRoomApiV1RoomsCurrentLeavePostMutation` | 없음 (body 불필요) | `LeaveRoomResponse` (`data: LeaveRoomMutation \| null`) | 성공 시 `/rooms`로 이동 |

## FR-006: 라우팅 및 접근 제어 (방 참가 여부 판단)

**REST API**

| 훅/함수 | 요청 타입 | 응답 타입 | 비고 |
| ------- | --------- | --------- | ---- |
| `meApiV1AuthMeGetOptions` | 없음 | `EnvelopeGuestInfoLoginCode` (`data: GuestInfo`) | `GuestInfo.current_case_id: string \| null` — null이면 방 미참가, 값 있으면 참가 중 |

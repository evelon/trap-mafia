# API 매핑: 방/로비 API 연동 및 라우팅 (MVP)

## FR-001 / FR-002: 방 참가 및 성공 시 화면 이동

**REST API**

| 훅/함수 | 요청 타입 | 응답 타입 | 비고 |
| ------- | --------- | --------- | ---- |
| `joinRoomApiV1RoomsRoomIdJoinPostMutation` | `JoinRoomApiV1RoomsRoomIdJoinPostData` (`path.room_id: string`) | `JoinRoomResponse` (`data: JoinRoomMutation \| null`) | MVP에서는 방 ID 하드코딩. `reason: 'JOINED' \| 'ALREADY_JOINED'` — 둘 다 성공으로 처리 가능 |

## FR-003: 방 자발적 퇴장

**REST API**

| 훅/함수 | 요청 타입 | 응답 타입 | 비고 |
| ------- | --------- | --------- | ---- |
| `leaveRoomApiV1RoomsCurrentLeavePostMutation` | 없음 (body 불필요) | `LeaveRoomResponse` (`data: LeaveRoomMutation \| null`) | 성공 시 `/rooms`로 이동 |

## FR-004: 라우팅 및 접근 제어 (방 참가 여부 판단)

**REST API**

| 훅/함수 | 요청 타입 | 응답 타입 | 비고 |
| ------- | --------- | --------- | ---- |
| `meApiV1AuthMeGetOptions` | 없음 | `EnvelopeGuestInfoLoginCode` (`data: GuestInfo`) | `GuestInfo.current_case_id: string \| null` — null이면 방 미참가, 값 있으면 참가 중 |

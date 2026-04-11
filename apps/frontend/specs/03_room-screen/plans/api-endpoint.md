# API 엔드포인트: 방 화면 (Room Screen)

## 엔드포인트/API 목록

| 요구사항 | 구분(REST/SSE) | 호출 방식 | 엔드포인트 |
| -------- | -------------- | --------- | ---------- |
| FR-001, FR-002, FR-003, FR-004: 방 정보·참가자·설정 실시간 표시 | SSE | `roomStateSseRtV1SseRoomsCurrentStateGet` | `GET /rt/v1/sse/rooms/current/state` |
| FR-005: 게임 시작 | REST | `caseStartApiV1RoomsCurrentCaseStartPostMutation` | `POST /api/v1/rooms/current/start-case` |
| FR-006: 게임 진행 중 판별 (SSE `room.case.started` 이벤트) | SSE | `roomStateSseRtV1SseRoomsCurrentStateGet` | `GET /rt/v1/sse/rooms/current/state` |
| FR-007: 방 나가기 | REST | `leaveRoomApiV1RoomsCurrentLeavePostMutation` | `POST /api/v1/rooms/current/leave` |
| FR-008: SSE 연결 오류 처리 | SSE | `roomStateSseRtV1SseRoomsCurrentStateGet` (에러 콜백) | `GET /rt/v1/sse/rooms/current/state` |
| SSE 스트림 종료 | REST | `closeRoomStateStreamRtV1SseRoomsCurrentClosePost` | `POST /rt/v1/sse/rooms/current/close` |

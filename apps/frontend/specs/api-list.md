# API 목록

전체 API 목록. 각 항목의 상세 매핑은 해당 스펙의 `plans/api-mapping.md`를 참조.

## REST API

| 이름 | 설명 | 엔드포인트 |
|------|------|-----------|
| `me` | 자신의 유저 정보 | `GET /api/v1/auth/me` |
| `guest_login` | username만으로 로그인 | `POST /api/v1/auth/guest-login` |
| `logout` | access 토큰 제거 | `POST /api/v1/auth/logout` |
| `refresh` | 토큰 refresh | `POST /api/v1/auth/refresh` |
| `join_room` | 방 입장 (멱등) | `POST /api/v1/rooms/{room_id}/join` |
| `leave_room` | 방 퇴장 (멱등) | `POST /api/v1/rooms/current/leave` |
| `kick_user` | 특정 사용자 강제 퇴장 | `POST /api/v1/rooms/current/users/{user_id}/kick` |
| `case_start` | 게임 시작 (case 생성) | `POST /api/v1/rooms/current/start-case` |
| `red_vote` | 게임 내 빨간(밤) 투표 | `POST /api/v1/cases/current/red-vote` |
| `init_blue_vote` | 파란(낮) 투표 대상 지정 | `POST /api/v1/cases/current/init-blue-vote` |
| `blue_vote` | 게임 내 파란(낮) 투표 | `POST /api/v1/cases/current/blue-vote` |
| `force_skip_discuss` | 토론 강제 진행 | `POST /api/v1/cases/current/force-skip-discuss` |
| `case_result` | 게임 결과 조회 | `GET /api/v1/cases/{case_id}/result` |

## SSE

| 이름 | 설명 | 엔드포인트 |
|------|------|-----------|
| `room_state` | 현재 방 상태 스트림 | `SSE /rt/v1/sse/rooms/current/state` |
| `case_state` | 현재 케이스 상태 스트림 | `SSE /rt/v1/sse/cases/current` |

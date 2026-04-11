# API 목록

전체 API 목록. 각 항목의 상세 매핑은 해당 스펙의 `plans/api-mapping.md`를 참조.

## REST API

| 이름 | 설명 | Path | Method |
|------|------|------|--------|
| `me` | 자신의 유저 정보 | `/api/v1/auth/me` | GET |
| `guest_login` | username만으로 로그인 | `/api/v1/auth/guest-login` | POST |
| `logout` | access 토큰 제거 | `/api/v1/auth/logout` | POST |
| `refresh` | 토큰 refresh | `/api/v1/auth/refresh` | POST |
| `join_room` | 방 입장 (멱등) | `/api/v1/rooms/{room_id}/join` | POST |
| `leave_room` | 방 퇴장 (멱등) | `/api/v1/rooms/current/leave` | POST |
| `kick_user` | 특정 사용자 강제 퇴장 | `/api/v1/rooms/current/users/{user_id}/kick` | POST |
| `case_start` | 게임 시작 (case 생성) | `/api/v1/rooms/current/start-case` | POST |
| `red_vote` | 게임 내 빨간(밤) 투표 | `/api/v1/cases/current/red-vote` | POST |
| `init_blue_vote` | 파란(낮) 투표 대상 지정 | `/api/v1/cases/current/init-blue-vote` | POST |
| `blue_vote` | 게임 내 파란(낮) 투표 | `/api/v1/cases/current/blue-vote` | POST |
| `force_skip_discuss` | 토론 강제 진행 | `/api/v1/cases/current/force-skip-discuss` | POST |
| `case_result` | 게임 결과 조회 | `/api/v1/cases/{case_id}/result` | GET |

## SSE

| 이름 | 설명 | Path |
|------|------|------|
| `room_state` | 현재 방 상태 스트림 | `/rt/v1/sse/rooms/current/state` |
| `case_state` | 현재 케이스 상태 스트림 | `/rt/v1/sse/cases/current` |

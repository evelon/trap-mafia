# Specs

피처 스펙 목록. 번호 순으로 구현 순서를 나타낸다.

## 스펙 목록

| 번호 | 디렉토리 | 범위 | API |
|------|----------|------|-----|
| 01 | `01_auth_mvp` | 게스트 인증 및 세션 관리 | `guest_login`, `logout`, `refresh`, `me` |
| 02 | `02_room-and-lobby-api-mvp` | 방 라우팅 + 참가/퇴장 (화면 UI 미포함, API 연동 및 라우팅만) | `join_room`, `leave_room` |
| 03 | _(미작성)_ | 방 화면 (SSE + 참가자 목록) | `room_state` (SSE) |
| 04 | _(미작성)_ | 게임 시작 + 게임 화면 SSE | `case_start`, `case_state` (SSE) |
| 05 | _(미작성)_ | 밤/낮 페이즈 투표 | `red_vote`, `init_blue_vote`, `blue_vote`, `force_skip_discuss` |
| 06 | _(미작성)_ | 게임 결과 | `case_result` |
| 07 | _(미작성)_ | 강퇴 | `kick_user` |

## 스펙 디렉토리 구조

```
{번호}_{feature}/
├── spec.md          # 피처 스펙 (사용자 시나리오, 요구사항)
└── plans/
    ├── plan.md      # 구현 계획
    └── api-mapping.md  # API 매핑
```

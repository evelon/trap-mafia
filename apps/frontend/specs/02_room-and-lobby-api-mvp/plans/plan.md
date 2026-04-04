# 구현 계획: 방/로비 API 연동 및 라우팅 (MVP)

## 요약

로비(`/rooms`)와 게임 방(`/rooms/current`) 두 화면에 대한 라우팅, 접근 제어, API 연동을 구현한다.

- **방 참가**: 로비에서 고정 방 ID로 `joinRoomApiV1RoomsRoomIdJoinPostMutation` 호출 → 성공 시 `/rooms/current`로 이동
- **퇴장**: `leaveRoomApiV1RoomsCurrentLeavePostMutation` 호출 → 성공 시 `/rooms`로 이동
- **라우팅 가드**: 미들웨어에서 쿠키 기반 로그인 여부, 페이지 진입 시 `meApiV1AuthMeGetOptions`의 `current_case_id`로 방 참가 여부 판단 → 리다이렉트

## 프로젝트 구조

### 생성/수정 파일 목록

```text
src/
├── app/
│   └── rooms/
│       ├── page.tsx                    (new)  # 로비 페이지 (/rooms)
│       └── current/
│           └── page.tsx                (new)  # 게임 방 페이지 (/rooms/current)
├── features/
│   ├── lobby/
│   │   └── JoinRoomButton.tsx          (new)  # 방 참가 버튼 (useMutation 포함)
│   └── room/
│       └── RoomView.tsx                (new)  # 방 화면 컨테이너 (퇴장 버튼)
└── middleware.ts                       (mod)  # 방 참가 여부 기반 리다이렉트 추가
```

## 설계 결정

| 결정 사항 | 선택한 방식 | 근거 |
| --------- | ----------- | ---- |
| 방 참가 여부 확인 위치 | 미들웨어 대신 페이지 컴포넌트에서 `useQuery(meApiV1AuthMeGetOptions)`로 확인 후 리다이렉트 | 미들웨어는 쿠키만 읽을 수 있어 `current_case_id` API 호출 불가. 페이지 진입 시 클라이언트 리다이렉트로 처리 |
| MVP 방 ID 하드코딩 위치 | `JoinRoomButton` 내부 상수 (`FIXED_ROOM_ID = "ffffffff-ffff-ffff-ffff-ffffffffffff"`) | 로비에는 방 선택 UI 없음. 향후 방 목록 기능 추가 시 props로 교체 |
| 미들웨어 역할 | 쿠키 기반 로그인 여부만 처리 (기존 유지) | `current_case_id`는 API 응답에만 있어 미들웨어에서 처리 불가 |

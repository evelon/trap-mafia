# 구현 계획: 방 화면 UI (Room Screen)

## 요약

방 화면(`/rooms/current`)에 SSE 기반 실시간 방 상태를 연동하고, 게임 시작·방 나가기 액션을 구현한다.

- **방 상태 수신**: `roomStateSseRtV1SseRoomsCurrentStateGet` SSE 훅(`useRoomSse`)으로 `RoomSnapshot`을 구독. 초기 스냅샷 및 이후 이벤트를 모두 이 단일 소스에서 처리
- **화면 구성**: 방 이름, 참가자 목록, 방 설정, 게임 시작/진행 중 상태, 방 나가기 버튼
- **게임 시작**: `caseStartApiV1RoomsCurrentCaseStartPostMutation` 호출. 화면 이동은 SSE `room.case.started` 이벤트 수신 시 (`last_event === 'room.case.started'`) 전체 참가자가 동시에 이동
- **연결 오류**: SSE `onSseError` + `sseMaxRetryAttempts` 초과 시 오류 UI 표시 및 새로고침·로비 이동 수단 제공

## 프로젝트 구조

### 생성/수정 파일 목록

```text
src/
├── features/
│   └── room/
│       ├── RoomClient.tsx              (mod)  # SSE 오류 경계 적용 (현재 stub)
│       ├── RoomView.tsx                (mod)  # 전체 방 화면 UI 구현
│       ├── useRoomSse.ts               (new)  # SSE 훅: RoomSnapshot 구독, 연결 상태 관리
│       ├── ParticipantList.tsx         (new)  # 참가자 목록 컴포넌트
│       └── RoomSettingsPanel.tsx       (new)  # 방 설정 표시 컴포넌트
└── shared/
    └── routes.ts                       (mod)  # CASES_CURRENT 경로 추가 (게임 화면 이동용)
```

### useRoomSse 훅 인터페이스 (설계)

```ts
type RoomSseState =
  | { status: 'connecting' }
  | { status: 'connected'; snapshot: RoomSnapshot }
  | { status: 'error'; snapshot: RoomSnapshot | null }   // 재연결 중 — 마지막 스냅샷 유지
  | { status: 'failed'; snapshot: RoomSnapshot | null }; // 최대 재시도 초과 — 수동 복구 안내

function useRoomSse(options: {
  onCaseStarted: () => void; // room.case.started 이벤트 수신 시 호출
}): RoomSseState;
```

- SSE 연결은 훅 마운트 시 시작, `AbortController`로 언마운트 시 종료
- `sseMaxRetryAttempts`를 설정해 초과 시 `failed` 상태로 전환

## 설계 결정

| 결정 사항 | 선택한 방식 | 근거 |
| --------- | ----------- | ---- |
| SSE 최대 재시도 횟수 | 5회 (지수 백오프, 최대 30초) | specs/README.md 공통 정책 — 재연결 실패 시 수동 복구 수단 제공. `sseMaxRetryAttempts: 5` |
| 게임 화면 이동 경로 | `/cases/current` (ROUTES.CASES_CURRENT) | spec 04에서 정의될 게임 화면의 경로. 이 스펙에서 경로 상수만 추가하고 페이지 구현은 spec 04에서 처리 |
| SSE 스트림 종료 시점 | 방 나가기 버튼 클릭 시 (`leaveRoom` mutation 호출 전) + 언마운트 시 AbortController | 방 나가기 직전 서버에 스트림 종료 알림 후 REST 호출. 언마운트는 AbortController로 처리 |
| 방 설정 표시 방식 | 전체 7개 필드 표시, 상세 보기 없이 단순 나열 | MVP. 복잡한 UI 불필요. 구현 시 필요에 따라 조정 가능 |
| `CaseStartRequest.red_player_count` | `null` 고정 | MVP — 팀 구성은 서버에서 자동 결정 |
| `RoomClient` 역할 | 인증 가드(기존) + SSE 연결 오류 시 fallback UI는 RoomView 내부에서 처리 | SSE 오류는 `failed` 상태로 인라인 처리. 별도 ErrorBoundary 추가 불필요 |

# 구현 계획: 방 화면 (Room Screen)

## 요약

방에 입장한 유저가 실시간으로 방 상태(참가자, 설정)를 확인하고, 게임 시작 및 방 나가기를 수행하는 화면을 구현한다. SSE(`room_state`) 스트림으로 `RoomSnapshot`을 수신하여 참가자 입장·퇴장을 즉시 반영하고, `room.case.started` 이벤트 수신 시 게임 화면으로 이동한다.

기술적으로는 SSE 연결을 관리하는 커스텀 훅(`useRoomSse`)을 작성하고, 이를 기반으로 방 화면 UI 컴포넌트를 구성한다. 연결 오류 시 재연결을 시도하며, 실패 시 사용자에게 새로고침/로비 이동 옵션을 제공한다.

## 프로젝트 구조

### 생성/수정 파일 목록

```text
src/
├── app/
│   └── (authed)/
│       └── rooms/
│           └── current/
│               └── page.tsx                     (mod)  # RoomClient import 유지 (변경 없을 수 있음)
├── features/
│   └── room/
│       ├── RoomClient.tsx                       (mod)  # SSE 연결 상태에 따른 분기 처리
│       ├── RoomView.tsx                         (mod)  # 전체 방 화면 레이아웃으로 확장
│       ├── RoomHeader.tsx                       (new)  # 헤더: 나가기 버튼, 방 이름, 설정 아이콘
│       ├── ParticipantGrid.tsx                  (new)  # 참가자 그리드 (4×2)
│       ├── ParticipantCard.tsx                  (new)  # 참가자 개별 카드
│       ├── RoomSettingsModal.tsx                (new)  # 방 설정 상세 모달
│       ├── StartGameButton.tsx                  (new)  # 게임 시작 버튼
│       ├── ConnectionErrorOverlay.tsx           (new)  # SSE 연결 오류 오버레이
│       └── useRoomSse.ts                        (new)  # SSE 연결 관리 훅
```

## 설계 결정

| 결정 사항 | 선택한 방식 | 근거 |
| --------- | ----------- | ---- |
| SSE 상태 관리 방식 | 커스텀 훅 `useRoomSse`에서 `useState`로 `RoomSnapshot` 관리 | SSE는 Suspense 대상이 아님 (`data-fetching-and-error-handling.md` 규칙). React Query 캐시 대신 로컬 상태로 최신 스냅샷을 유지하는 것이 SSE 스트림 특성에 적합 |
| SSE 재연결 전략 | `createSseClient`의 내장 지수 백오프 사용 (기본 3초, 최대 30초) + `sseMaxRetryAttempts` 설정 | 자동 생성된 SSE 클라이언트가 재연결 로직을 이미 지원. 별도 구현 불필요 |
| 연결 오류 표시 방식 | 참가자 영역 위에 오버레이 (`ConnectionErrorOverlay`) | 와이어프레임 설계를 따름. 재연결 중/실패 상태를 분리하여 표시 |
| 게임 화면 이동 트리거 | SSE `room.case.started` 이벤트 수신 시 라우터로 이동 | 스펙 Clarification에서 확정. 모든 참가자가 동일 시점에 이동하기 위함 |
| 참가자 그리드 레이아웃 | 8칸 고정 그리드 (4열 × 2행), `max_players` 기준 | 와이어프레임 설계를 따름. 빈 칸은 빈 상태 카드로 표시 |
| 방 설정 모달 | shadcn Dialog 컴포넌트 사용 | 기존 shadcn-ui 컴포넌트 활용. 읽기 전용 표시만 필요하므로 단순 Dialog로 충분 |
| `RoomView` 리팩토링 범위 | 기존 `RoomView`를 방 화면 전체 레이아웃 컨테이너로 확장 | 기존 코드가 leave 버튼만 있는 최소 구현이므로, 와이어프레임 기반으로 전면 재작성 |
| SSE 연결 시작/종료 시점 | `useRoomSse` 훅에서 `useEffect`로 마운트 시 연결, 언마운트 시 `AbortController`로 해제 + `closeRoomStateStream` 호출 | 방 화면 진입 시 연결, 이탈 시 정리. 서버에 스트림 종료를 알림 |
| 게임 진행 중 진입 처리 | SSE 최초 `room.connected` 스냅샷의 `current_case`가 존재하면 즉시 게임 화면 이동 | FR-006 요구사항. 별도 API 호출 없이 SSE 초기 스냅샷으로 판별 가능 |

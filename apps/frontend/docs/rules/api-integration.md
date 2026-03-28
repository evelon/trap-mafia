# API 연동 가이드

## 개요

백엔드 API 연동은 `@hey-api/openapi-ts`로 자동 생성된 코드를 사용한다. 생성 코드는 `src/client/gen/`에 위치하며 직접 수정하지 않는다.

## REST API

### 사용 방법

`src/client/gen/@tanstack/react-query.gen.ts`에서 생성된 훅을 사용한다.

**조회 (Query)**:

```tsx
import { someQueryOptions } from "@/client/gen";

// 컴포넌트 내에서
const { data, isLoading } = useQuery({
  ...someQueryOptions(),
  // 필요시 추가 옵션 오버라이드
});
```

**변경 (Mutation)**:

```tsx
import { someMutation } from "@/client/gen";

const mutation = useMutation({
  ...someMutation(),
  onSuccess: () => { /* 성공 처리 */ },
});

mutation.mutate({ body: { ... } });
```

### 생성 파일 역할

| 파일                           | 역할                     | 사용 시점                                   |
| ------------------------------ | ------------------------ | ------------------------------------------- |
| `@tanstack/react-query.gen.ts` | Query/Mutation 훅 팩토리 | 컴포넌트에서 API 호출 시 (주로 사용)        |
| `sdk.gen.ts`                   | 저수준 API 함수          | 훅 외부에서 직접 호출 필요 시 (인터셉터 등) |
| `types.gen.ts`                 | 요청/응답 타입           | 타입 참조 시                                |
| `zod.gen.ts`                   | Zod 검증 스키마          | 폼 검증, 런타임 검증 시                     |

### 인증 처리

- Axios 인스턴스에 `withCredentials: true` 설정 (`src/client/axios-config.ts`)
- 401 응답 시 자동 토큰 리프레시 + 원래 요청 재시도 (`src/client/axios-interceptor.ts`)
- 리프레시 실패 시 `/login`으로 리다이렉트
- 인증 상태 조회는 `useAuthSuspense()` 또는 `useAuth()` 훅 사용 (`src/features/login/`)
- Suspense/Error Boundary 패턴은 `docs/rules/data-fetching-and-error-handling.md` 참조

## SSE (Server-Sent Events)

### 사용 방법

`sdk.gen.ts`의 SSE 엔드포인트 함수를 사용한다. 내부적으로 `fetch` 기반의 `createSseClient`를 사용하며 Axios를 거치지 않는다.

```tsx
import { roomStateSseRtV1SseRoomsCurrentStateGet } from "@/client/gen";
```

### SSE 클라이언트 특징

- `src/client/gen/core/serverSentEvents.gen.ts`에 구현
- `fetch` API 기반 (Axios 아님)
- `AsyncGenerator`로 이벤트 스트림 반환
- 자동 재연결: 지수 백오프 (기본 3초, 최대 30초)
- 콜백: `onSseEvent`, `onSseError`
- `AbortController`로 연결 해제

### 현재 SSE 엔드포인트

| 함수                                               | 경로                                  | 설명            |
| -------------------------------------------------- | ------------------------------------- | --------------- |
| `roomStateSseRtV1SseRoomsCurrentStateGet`          | `GET /rt/v1/sse/rooms/current/state`  | 방 상태 스트림  |
| `closeRoomStateStreamRtV1SseRoomsCurrentClosePost` | `POST /rt/v1/sse/rooms/current/close` | SSE 스트림 종료 |

### 주의사항

- SSE는 `fetch` 기반이므로 Axios 인터셉터(토큰 리프레시 등)가 적용되지 않는다
- 인증이 필요한 SSE 엔드포인트는 쿠키 기반 인증을 사용한다 (credentials 설정 필요)

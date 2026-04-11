---
description: API 클라이언트 계층 사용법: 코드 생성, REST, SSE, 인증 처리
paths: ["src/client/**", "src/features/**", "src/app/**"]
---

# API 연동 가이드

## 자동 생성 코드

- 코드 생성: `pnpm openapi-ts` (설정: `openapi-ts.config.ts`)
- 생성 코드는 `src/client/gen/`에 위치하며 **절대** 직접 수정하지 않는다.

## REST API

- `src/client/gen/@tanstack/react-query.gen.ts`의 옵션 팩토리(`~QueryOptions`, `~Mutation`)를 `useQuery`/`useMutation`에 스프레드해서 사용한다.

## 인증 처리

- API 클라이언트에 `withCredentials: true` 설정 (`src/client/client-config.ts`)
- 401 응답 시 자동 토큰 리프레시 + 원래 요청 재시도 (`src/client/axios-interceptor.ts`)
- 리프레시 실패 시 `/login`으로 리다이렉트
- 인증 상태 조회는 `useAuthSuspense()` 또는 `useAuth()` 훅 사용 (`src/features/login/`)

## SSE (Server-Sent Events)

- `createSseClient`(`src/client/gen/core/serverSentEvents.gen.ts`)를 사용한다.
- `fetch` API 기반이므로 Axios 인터셉터(토큰 리프레시 등)가 적용되지 않는다.
- 인증이 필요한 SSE 엔드포인트는 쿠키 기반 인증을 사용한다 (`credentials: "include"`).

---
description: API 클라이언트 인프라: 코드 생성, 클라이언트 설정, interceptor, SSE 클라이언트
paths: ["src/client/**"]
---

# API 클라이언트

## 자동 생성 코드

- 코드 생성: `pnpm openapi-ts` (설정: `openapi-ts.config.ts`)
- 생성 코드는 `src/client/gen/`에 위치하며 **절대** 직접 수정하지 않는다.

## 클라이언트 설정

- `withCredentials: true` 설정 (`src/client/client-config.ts`)
- 401 응답 시 자동 토큰 리프레시 + 원래 요청 재시도 (`src/client/axios-interceptor.ts`)
- 리프레시 실패 시 `/login`으로 리다이렉트

## SSE (Server-Sent Events)

- `createSseClient`(`src/client/gen/core/serverSentEvents.gen.ts`)를 사용한다.
- `fetch` API 기반이므로 Axios 인터셉터(토큰 리프레시 등)가 적용되지 않는다.
- 인증이 필요한 SSE 엔드포인트는 쿠키 기반 인증을 사용한다 (`credentials: "include"`).

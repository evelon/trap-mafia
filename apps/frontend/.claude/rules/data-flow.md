---
description: 라우트 구조, 인증 흐름, Suspense/Error Boundary 패턴
paths: ["src/features/**", "src/app/**"]
---

# 데이터 흐름 및 에러 처리 패턴

## 라우트 구조

인증 필요 페이지는 `(authed)/`, 공개 페이지는 `(public)/` 하위에 추가한다.

## 인증 (Auth)

| 훅 | 사용 위치 |
|----|-----------|
| `useAuthSuspense()` | `(authed)` 하위 페이지·컴포넌트 |
| `useAuth()` | 로그인 폼 등 비인증 컨텍스트 |

- `(authed)` 하위에서는 항상 `useAuthSuspense()`를 사용한다.

### 인증 흐름 (3단계)

인증은 middleware → Query → interceptor 3개 레이어로 처리된다. 각 레이어가 담당하는 역할이 다르므로 중복 처리하지 않는다.

1. **middleware** (쿠키 체크): 토큰 없으면 `/login` 리다이렉트
2. **`useSuspenseQuery(/auth/me)`**: 토큰 유효성 검증 + user 데이터 로드
3. **axios interceptor**: 401 응답 시 `/login` 리다이렉트 — 이 에러는 `error.tsx`에 도달하지 않는다

## 데이터 유형별 로딩·에러 처리

- **Query(조회)**: `useSuspenseQuery`를 사용하고, 로딩은 Suspense boundary에 위임한다. 에러는 `error.tsx` 또는 Error Boundary에서 처리한다.
- **Mutation(변경)**: Suspense 대상이 아니다. `isPending`으로 로딩, `onError` 콜백으로 에러를 직접 처리한다.
- **SSE**: Suspense 대상이 아니다. 커스텀 훅 내부에서 `isConnected`/`isError` 상태로 직접 처리한다.

## Suspense / Error Boundary

- `(authed)/loading.tsx`가 기본 Suspense fallback이다. 독립 로딩 영역이 필요하면 `<Suspense>`로 추가 분리한다.
- `(authed)/error.tsx`가 비인증 에러(서버 에러, 네트워크 에러 등)를 처리한다. 페이지를 벗어나지 않아야 하는 에러는 별도 Error Boundary로 감싼다.

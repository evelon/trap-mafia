# 데이터 페칭 및 에러 처리 가이드

## 라우트 구조

인증 여부에 따라 라우트 그룹을 분리한다. URL에는 영향을 주지 않는다.

```
src/app/
├── layout.tsx              # 루트 레이아웃 (Providers, Toaster)
├── (public)/               # 비인증 페이지
│   └── login/page.tsx
├── (authed)/               # 인증 필수 페이지
│   ├── layout.tsx          # authed 레이아웃
│   ├── loading.tsx         # Suspense fallback (로딩 UI)
│   ├── error.tsx           # Error Boundary (401 → /login 리다이렉트)
│   └── rooms/...
```

새로운 인증 필요 페이지는 `(authed)/` 하위에 추가한다. 공개 페이지는 `(public)/` 하위에 추가한다.

## 인증 (Auth)

### 훅 선택 기준

| 훅 | 반환 타입 | 사용 위치 |
|----|-----------|-----------|
| `useAuthSuspense()` | `{ user: GuestInfo, logout }` — user non-nullable | `(authed)` 하위 페이지·컴포넌트 |
| `useAuth()` | `{ user: GuestInfo \| null, isLoading, isError, logout }` | 로그인 폼 등 비인증 컨텍스트 |

- `(authed)` 하위에서는 항상 `useAuthSuspense()`를 사용한다.
- `useAuthSuspense()`는 `useSuspenseQuery` 기반이므로 데이터가 준비될 때까지 Suspense boundary에서 대기한다.
- `user`가 non-nullable이므로 `isLoading` 분기나 optional chaining이 필요 없다.

### 인증 흐름

```
middleware (쿠키 체크)
  ├─ 토큰 없음 → /login 리다이렉트
  └─ 토큰 있음 → 페이지 진입
       └─ useSuspenseQuery(/auth/me)
            ├─ 성공 → user 데이터 반환, 컴포넌트 렌더링
            └─ 실패 (401) → error.tsx에서 /login 리다이렉트
```

## Suspense

### 원칙

- **Query(조회)**: `useSuspenseQuery`를 사용하고, 로딩 상태는 Suspense boundary에 위임한다.
- **Mutation(변경)**: Suspense 대상이 아니다. `useMutation`의 `isPending`으로 직접 처리한다.
- **SSE**: Suspense 대상이 아니다. 커스텀 훅 내부에서 `isConnected`/`isError` 상태로 직접 처리한다.

### Suspense boundary 계층

```
(authed)/loading.tsx        ← 페이지 전환 시 자동 Suspense fallback
  └─ 페이지 컴포넌트
       └─ 필요시 <Suspense>로 하위 영역 분리 가능
```

- Next.js가 `loading.tsx`를 자동으로 Suspense boundary로 래핑한다.
- 페이지 내에서 독립적으로 로딩되어야 하는 영역이 있으면 `<Suspense fallback={...}>`로 추가 분리한다.

### Query 사용 예시

```tsx
// (authed) 하위 페이지에서의 데이터 조회
import { useSuspenseQuery } from "@tanstack/react-query";
import { someQueryOptions } from "@/client/gen/@tanstack/react-query.gen";

function MyComponent() {
  const { data } = useSuspenseQuery({
    ...someQueryOptions(),
  });
  // data는 항상 존재 — isLoading 분기 불필요
}
```

## Error Boundary

### 페이지 레벨: `error.tsx`

`(authed)/error.tsx`가 인증 필요 페이지의 에러를 처리한다.

- **401 에러**: `/login`으로 자동 리다이렉트 (axios interceptor의 토큰 리프레시도 실패한 경우)
- **기타 에러**: 에러 메시지 + "다시 시도" 버튼 (`reset()` 호출)

### 하위 컴포넌트 레벨

페이지 전체가 아닌 특정 영역만 에러 처리가 필요한 경우, 별도의 Error Boundary 컴포넌트로 감싼다. SSE 연결 실패 등 페이지를 벗어나지 않아야 하는 에러가 해당된다.

현재 `RoomView`의 SSE 에러는 컴포넌트 내부에서 직접 처리하고 있다 (`isError` 상태 → 에러 UI 렌더링).

## 정리: 데이터 유형별 처리 방식

| 유형 | 로딩 처리 | 에러 처리 |
|------|-----------|-----------|
| Query (조회) | `useSuspenseQuery` + Suspense boundary | `error.tsx` (페이지) 또는 Error Boundary (하위) |
| Mutation (변경) | `isPending` 직접 처리 | `onError` 콜백 (toast 등) |
| SSE | 커스텀 훅 내부 상태 | 커스텀 훅 내부 상태 또는 Error Boundary |
| Auth | `useAuthSuspense` + Suspense boundary | `error.tsx` (401 → 리다이렉트) |

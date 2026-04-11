# Auth 설계 스펙

## 1. 인증 방식

**HttpOnly Cookie + JWT** 기반 인증.

- 서버가 `Set-Cookie`로 토큰 발급/제거
- 프론트엔드는 토큰 값을 직접 다루지 않음 (XSS 안전)
- `withCredentials: true`로 쿠키 자동 전송

```
Browser                         Server (FastAPI)
  │                                │
  │  POST /auth/guest-login       │
  │  { username }  ──────────────>│
  │                                │── JWT 생성
  │  Set-Cookie: access_token     │
  │  Set-Cookie: refresh_token    │
  │  <────────────────────────────│
  │                                │
  │  이후 모든 요청                  │
  │  Cookie: access_token  ──────>│  (자동 전송)
```

### 쿠키 목록

| 쿠키             | 용도                    | 발급 시점        | 제거 시점          |
| ---------------- | ----------------------- | ---------------- | ------------------ |
| `access_token`   | API 인증 (단수명 JWT)   | login, refresh   | logout (Max-Age=0) |
| `refresh_token`  | access_token 갱신       | login            | logout (Max-Age=0) |

---

## 2. API 엔드포인트

모든 Auth API는 `@hey-api/openapi-ts`로 자동 생성되어 있음.

| 메서드 | 경로                       | 설명                          | 요청 Body                | 응답 Data     |
| ------ | -------------------------- | ----------------------------- | ------------------------ | ------------- |
| POST   | `/api/v1/auth/guest-login` | 게스트 로그인 (쿠키 발급)     | `{ username: string }`   | `GuestInfo`   |
| GET    | `/api/v1/auth/me`          | 현재 유저 조회 (쿠키로 인증)  | -                        | `GuestInfo`   |
| POST   | `/api/v1/auth/refresh`     | access_token 갱신             | -                        | `GuestInfo`   |
| POST   | `/api/v1/auth/logout`      | 로그아웃 (쿠키 제거)          | -                        | -             |

### GuestInfo 타입

```ts
type GuestInfo = {
  id: string;            // UUID
  username: string;
  in_case: boolean;
  current_case_id?: string | null;
};
```

### 공통 응답 Envelope

```ts
type Envelope<T, C> = {
  ok: boolean;
  code: C;
  message?: string | null;
  data?: T | null;
  meta?: Record<string, unknown> | null;
};
```

### 에러 코드

| HTTP | code                       | 의미                    |
| ---- | -------------------------- | ----------------------- |
| 401  | `AUTH_TOKEN_NOT_INCLUDED`  | 쿠키에 토큰 없음       |
| 401  | `AUTH_TOKEN_INVALID`       | 토큰 검증 실패         |
| 401  | `AUTH_TOKEN_EXPIRED`       | 토큰 만료              |
| 401  | `AUTH_USER_NOT_FOUND`      | 토큰의 유저가 DB에 없음 |

---

## 3. 상태 관리

Zustand/Context 없이 **React Query 캐시를 Single Source of Truth**로 사용.

```
React Query Cache
  queryKey: ["meApiV1AuthMeGet"]
  data: GuestInfo | undefined
         │
         ▼
  useAuth() 커스텀 훅
  ├── user: GuestInfo | null
  ├── isLoggedIn: boolean
  ├── isLoading: boolean
  ├── login(username)
  ├── logout()
  └── refresh()
```

### useAuth 훅 설계

```ts
function useAuth() {
  const queryClient = useQueryClient();
  const router = useRouter();

  // 현재 유저 조회 (GET /me)
  const { data, isLoading, isError } = useQuery({
    ...meApiV1AuthMeGetOptions(),
    retry: false,
  });

  const user = data?.data ?? null;
  const isLoggedIn = !!user;

  // 로그인
  const loginMutation = useMutation({
    ...guestLoginApiV1AuthGuestLoginPostMutation(),
    onSuccess: (res) => {
      queryClient.setQueryData(meApiV1AuthMeGetQueryKey(), res);
      if (res.data?.in_case) {
        router.push(`/case/${res.data.current_case_id}`);
      } else {
        router.push("/rooms");
      }
    },
  });

  // 로그아웃
  const logoutMutation = useMutation({
    ...logoutApiV1AuthLogoutPostMutation(),
    onSuccess: () => {
      queryClient.clear();
      router.push("/login");
    },
  });

  return { user, isLoggedIn, isLoading, loginMutation, logoutMutation };
}
```

---

## 4. 401 자동 갱신 (Axios Interceptor)

`axios-interceptor.ts`에 response interceptor를 추가하여 access_token 만료 시 자동 refresh.

```
요청 → 401 응답
  │
  ├─ refresh 이미 진행 중? → 큐에 대기 (Promise)
  │
  └─ POST /auth/refresh
       ├─ 성공 → 큐의 대기 요청 + 원래 요청 재시도
       └─ 실패 → queryClient.clear() + /login 리다이렉트
```

### 핵심 규칙

- **동시 다발 401**: refresh 호출은 **1회만**, 나머지는 큐에서 대기
- **refresh 자체가 401**: 완전 만료 → 로그인 페이지로 이동
- `/auth/refresh`, `/auth/guest-login` 요청은 interceptor에서 **제외**

### 구현 스케치

```ts
let isRefreshing = false;
let failedQueue: { resolve: Function; reject: Function }[] = [];

function processQueue(error: any) {
  failedQueue.forEach(({ resolve, reject }) => {
    error ? reject(error) : resolve();
  });
  failedQueue = [];
}

// response interceptor
client.instance.interceptors.response.use(
  (res) => res,
  async (error) => {
    const originalRequest = error.config;

    // refresh/login 요청은 제외
    if (originalRequest.url?.includes("/auth/refresh") ||
        originalRequest.url?.includes("/auth/guest-login")) {
      return Promise.reject(error);
    }

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // 큐에 대기
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(() => client.instance(originalRequest));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        await refreshApiV1AuthRefreshPost();
        processQueue(null);
        return client.instance(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError);
        // → /login 리다이렉트 (queryClient.clear)
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);
```

---

## 5. 라우트 보호

**2단계 보호** 전략.

### 5-1. Next.js Middleware (서버 레벨)

`middleware.ts`에서 쿠키 **존재 여부**만 체크.
HttpOnly 쿠키는 값을 읽을 수 없으므로 존재 여부로 판단.

```ts
// middleware.ts
const PUBLIC_PATHS = ["/login"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (PUBLIC_PATHS.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  const accessToken = request.cookies.get("access_token");
  if (!accessToken) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
```

### 5-2. 클라이언트 Auth Guard (레이아웃)

실제 토큰 유효성은 클라이언트에서 `useAuth()` → `GET /me`로 확인.

```
app/
├── login/page.tsx              ← 공개
└── (authenticated)/
    ├── layout.tsx              ← useAuth() 가드
    └── rooms/page.tsx          ← 인증 필요
```

```ts
// app/(authenticated)/layout.tsx
function AuthLayout({ children }) {
  const { isLoggedIn, isLoading } = useAuth();

  if (isLoading) return <Spinner />;
  if (!isLoggedIn) {
    redirect("/login");
    return null;
  }

  return <>{children}</>;
}
```

---

## 6. 시나리오별 플로우

### 6-1. 로그인

```
/login 페이지
  │
  │ form submit { username: "moon" }
  ▼
useMutation(guestLoginMutation)
  → POST /auth/guest-login
  → 서버: Set-Cookie (access_token + refresh_token)
  → onSuccess:
      setQueryData(meQueryKey, response)
      in_case? → /case/:id
      else     → /rooms
```

### 6-2. 페이지 진입 (인증 확인)

```
(authenticated)/rooms 진입
  │
  ├─ middleware: access_token 쿠키 있음? → YES → 통과
  │                                        NO  → /login redirect
  ▼
  AuthLayout: useAuth()
    → GET /me
    ├─ 200: user 데이터 확인 → 렌더링
    └─ 401: interceptor가 refresh 시도
            ├─ refresh 성공 → me 재시도 → 렌더링
            └─ refresh 실패 → /login redirect
```

### 6-3. 토큰 만료 (자동 갱신)

```
API 호출 중 401 발생
  │
  ▼
axios interceptor
  → POST /auth/refresh (refresh_token 쿠키)
  ├─ 성공: 새 access_token 쿠키 → 원래 요청 재시도
  └─ 실패: /login redirect
```

### 6-4. 로그아웃

```
logout 버튼 클릭
  │
  ▼
useMutation(logoutMutation)
  → POST /auth/logout
  → 서버: Set-Cookie Max-Age=0 (쿠키 삭제)
  → onSuccess:
      queryClient.clear()
      router.push("/login")
```

---

## 7. 구현할 파일 목록

| 파일                                     | 작업     | 설명                              |
| ---------------------------------------- | -------- | --------------------------------- |
| `src/hooks/useAuth.ts`                   | **신규** | 인증 커스텀 훅                    |
| `src/client/client-config.ts`            | **수정** | 401 interceptor 추가              |
| `src/middleware.ts`                       | **신규** | 쿠키 존재 여부 기반 라우트 보호   |
| `src/app/(authenticated)/layout.tsx`     | **신규** | 클라이언트 auth guard 레이아웃    |
| `src/components/login/LoginForm.tsx`     | **수정** | useAuth 연동, 리다이렉트 활성화  |

### 의존 관계 (구현 순서)

```
1. client-config.ts (interceptor)
2. useAuth.ts (훅)
3. middleware.ts
4. (authenticated)/layout.tsx
5. LoginForm.tsx (수정)
```

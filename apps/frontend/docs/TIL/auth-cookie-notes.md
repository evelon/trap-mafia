# 인증 쿠키 학습 노트

## 1. http-only 쿠키

쿠키에는 두 종류가 있다.

### 일반 쿠키
```
Set-Cookie: token=abc123
```
- JavaScript에서 `document.cookie`로 읽을 수 있음
- XSS 공격으로 토큰 탈취 가능

### http-only 쿠키
```
Set-Cookie: access_token=abc123; HttpOnly
```
- JavaScript에서 **읽을 수 없음** (브라우저가 차단)
- HTTP 요청/응답에서만 오고감
- XSS 공격으로 탈취 불가 → 보안상 안전

```
JS에서 접근 시도:
document.cookie  →  "" (access_token 보이지 않음)

실제 HTTP 요청:
GET /api/...
Cookie: access_token=abc123  ← 브라우저가 자동으로 붙여줌
```

> **결과**: 토큰을 JS가 직접 만질 수 없어서 안전하지만,
> FE에서 로그인 여부를 쿠키로 판단할 수 없으므로 별도 상태 관리가 필요하다.

---

## 2. 쿠키의 기본 동작

쿠키는 **설정해준 도메인에 요청할 때 자동으로 붙는다.** 이건 브라우저의 기본 동작이다.

```
1. 사용자가 naver.com 접속
2. 서버: Set-Cookie: session=abc  (naver.com 도메인)
3. 이후 naver.com에 요청할 때마다 → Cookie: session=abc 자동 포함
```

---

## 3. withCredentials

### 언제 필요한가

**페이지 탐색(주소창 이동)** 이 아닌, **JS로 보내는 HTTP 요청(fetch/XHR/axios)** 에만 해당되는 이야기다.

브라우저는 JS로 보내는 **cross-origin** 요청에서 쿠키를 기본적으로 제외한다.

```
axios.post("http://localhost:8000/api/...")  →  cross-origin (포트가 다름)

withCredentials: false (기본값)
  → 8000 도메인 쿠키가 저장소에 있어도, 요청에 안 붙임

withCredentials: true
  → 8000 도메인 쿠키를 요청에 포함시킴
```

### withCredentials: false가 기본값인 이유

보안 때문이다. 이를 **CSRF(Cross-Site Request Forgery)** 방어라고 한다.

```
시나리오:
1. 사용자가 mybank.com 로그인 → 쿠키 발급
2. 악성 사이트 evil.com 접속
3. evil.com JS가 mybank.com/transfer?to=hacker 요청

withCredentials: false (기본)
  → mybank.com 쿠키 안 붙음 → 서버가 인증 실패 처리 → 안전

withCredentials: true
  → mybank.com 쿠키 붙음 → 서버가 정상 인증된 요청으로 처리 → 위험
```

**의도하지 않은 cross-origin 요청에 내 쿠키가 실려가는 것을 막기 위해** 기본값이 false다.
우리 앱처럼 FE가 BE에 의도적으로 쿠키를 보내야 하는 상황에서만 명시적으로 true로 설정한다.

---

## 4. 서버 조건 (CORS)

`withCredentials: true` 만으로는 부족하다. 서버도 허용해야 한다.

```
서버 응답 헤더에 필요:
  Access-Control-Allow-Credentials: true
  Access-Control-Allow-Origin: http://localhost:3000  ← * 는 안 됨
```

`*`(와일드카드)로 origin을 허용하면 credentials와 함께 사용할 수 없다. 특정 origin을 명시해야 한다.

---

## 5. 전체 흐름 요약

```
1. FE → BE: POST /auth/guest-login (withCredentials: true)
2. BE → FE: 200 OK
            Set-Cookie: access_token=...; HttpOnly; Secure; SameSite=Lax
            body: { id, username, in_case, current_case_id }
3. 브라우저: BE 도메인에 access_token 쿠키 저장
4. 이후 FE → BE 모든 요청: 브라우저가 쿠키 자동 포함
5. BE: 쿠키에서 토큰 검증 → 인증 처리
```

FE에서 쿠키(토큰)를 직접 읽을 수 없으므로, 로그인 응답 body의 유저 정보를 별도 상태(예: Zustand)로 관리한다.

---

## 6. 토큰 만료와 갱신

### 만료 시간은 서버가 정한다

토큰의 만료 시간은 **서버가 JWT를 생성할 때 결정**한다. 프론트엔드가 정하는 것이 아니다.

```
서버가 JWT 생성 시:
  access_token  → exp: 현재시각 + 30분 (짧게)
  refresh_token → exp: 현재시각 + 7일  (길게)
```

쿠키의 `Max-Age`도 서버가 `Set-Cookie` 헤더에서 설정한다. 브라우저는 이 값에 따라 쿠키를 자동으로 만료/삭제한다.

### 왜 두 개로 나누는가

access token 하나만 쓰면, 만료될 때마다 다시 로그인해야 한다.
refresh token을 함께 두면, access token이 만료돼도 **자동으로 새로 발급**받을 수 있다.

access token을 짧게 유지하는 이유는, 탈취되더라도 피해 시간을 최소화하기 위해서다.

```
access token만 사용:
  만료 → 로그인 다시 해야 함 → 사용자 경험 나쁨

access + refresh 조합:
  access 만료 → refresh로 자동 갱신 → 사용자는 모름
  refresh 만료 → 그때 로그인 → 자주 안 일어남
```

### 토큰 만료 시 FE 대응 전략

```
API 요청 → 서버 응답 확인
  │
  ├─ 200 OK → 정상 처리
  │
  └─ 401 Unauthorized (access token 만료)
       │
       ├─ POST /auth/refresh 시도 (refresh token은 아직 유효)
       │    ├─ 성공 → 서버가 새 access_token 쿠키 발급
       │    │         원래 요청 재시도 → 사용자는 아무것도 모름
       │    │
       │    └─ 실패 (refresh token도 만료)
       │         → 세션 완전 종료
       │         → queryClient.clear() + /login 리다이렉트
       │
       └─ 이 과정을 axios interceptor로 자동화
```

| 상황 | 대응 | 사용자 경험 |
|------|------|------------|
| access token 만료 | refresh 요청 → 자동 재발급 | 사용자는 모름 (투명하게 처리) |
| refresh token도 만료 | /login으로 이동 | 다시 로그인 필요 |

> **핵심**: 401을 받으면 refresh를 먼저 시도하고, 그것도 실패하면 로그인으로 보낸다.
> 이 로직은 axios response interceptor에서 처리하며, 우리 프로젝트에서는 다음 PR에서 구현 예정.

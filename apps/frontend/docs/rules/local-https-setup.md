# 로컬 HTTPS 개발 환경 설정

## 배경

백엔드는 Caddy 리버스 프록시를 통해 `https://localhost`로 서비스된다.
Caddy는 기본적으로 자체 로컬 CA로 TLS 인증서를 자동 발급(auto-TLS)한다.

문제는 Next.js SSR 시 Node.js가 `https://localhost`로 API 요청을 보낼 때 발생한다.
Node.js는 시스템 trust store를 사용하지 않기 때문에 Caddy의 자체 CA를 신뢰하지 않아
`unable to get local issuer certificate` 에러가 발생한다.

## 해결 방법

[mkcert](https://github.com/FiloSottile/mkcert)로 신뢰할 수 있는 로컬 인증서를 발급해
Caddy가 이를 사용하도록 하고, Node.js에도 동일한 CA를 신뢰하도록 설정한다.

## 최초 설정 (신규 개발 머신)

### 1. mkcert 설치 및 로컬 CA 등록

```bash
brew install mkcert
mkcert -install   # macOS 키체인 + 브라우저 trust store에 로컬 CA 등록
```

### 2. localhost 인증서 생성

```bash
cd infra/edge/caddy/certs
mkcert localhost
```

`localhost.pem`과 `localhost-key.pem`이 생성된다.
이 파일들은 `.gitignore`의 `*.pem` 규칙에 의해 git에 포함되지 않는다.

### 3. Caddy 컨테이너 재시작

```bash
COMPOSE_PROJECT_NAME=trap-mafia-v4 docker compose \
  --env-file ops/env/compose.host.env \
  -f ops/compose/host/compose.yml \
  up -d --no-deps --force-recreate caddy
```

또는 Makefile을 사용하는 경우:

```bash
make host-up-only
```

## 동작 원리

| 구성 요소 | 역할 |
|---|---|
| `mkcert -install` | 로컬 CA를 macOS 키체인 + 브라우저에 등록 |
| `infra/edge/caddy/certs/localhost.pem` | Caddy가 사용하는 TLS 인증서 |
| `Caddyfile.host`의 `tls` 디렉티브 | Caddy auto-TLS 대신 mkcert 인증서 직접 지정 |
| `package.json`의 `dev:https` 스크립트 | `NODE_EXTRA_CA_CERTS`를 주입해 Node.js(SSR)가 mkcert CA를 신뢰하도록 설정 |

```
브라우저  ──────────────────────► https://localhost (Caddy, mkcert 인증서)
                                          │
                           ┌──────────────┼──────────────┐
                           ▼              ▼              ▼
                      /api/*          /rt/*            /*
                    BE:8000         BE:8000       FE:3000 (pnpm dev:https)
                                                      │
                                            NODE_EXTRA_CA_CERTS 주입
                                           → SSR 시 mkcert CA 신뢰
```

## 원복 방법

```bash
# 1. 변경된 파일 원복
git restore infra/edge/caddy/Caddyfile.host
git restore ops/compose/host/compose.yml
git restore apps/frontend/package.json

# 2. Caddy 재생성 (auto-TLS로 복귀)
COMPOSE_PROJECT_NAME=trap-mafia-v4 docker compose \
  --env-file ops/env/compose.host.env \
  -f ops/compose/host/compose.yml \
  up -d --no-deps --force-recreate caddy

# 3. mkcert 제거 (선택)
mkcert -uninstall
brew uninstall mkcert
```

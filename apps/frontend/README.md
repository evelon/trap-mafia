# Frontend

## 사전 준비

백엔드 서버가 먼저 실행되어야 합니다. **프로젝트 루트 경로**에서:

```bash
make host-up    # 인프라(DB 등) 실행. **db 마이그레이션도 포함**
make host-be    # 백엔드 서버 실행
```

## 실행

```bash
pnpm dev:https
```

SSR에서 API를 호출할 때 Node.js가 mkcert CA를 신뢰하도록 `NODE_EXTRA_CA_CERTS`를 설정한다. `pnpm dev`로 실행하면 새로고침 시 SSR API 호출에서 TLS 인증서 오류가 발생한다.

## 기타 주요 스크립트

| 명령어               | 설명                                   |
| -------------------- | -------------------------------------- |
| `npm install`        | 의존성 설치                            |
| `npm run lint`       | ESLint 검사                            |
| `npm run check-type` | 타입 검사                              |
| `npm run format`     | Prettier 포맷팅                        |
| `npm run openapi-ts` | OpenAPI 타입 생성                      |

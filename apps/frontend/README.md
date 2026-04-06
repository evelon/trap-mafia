# Frontend

## 사전 준비

백엔드 서버가 먼저 실행되어야 합니다. **프로젝트 루트 경로**에서:

```bash
make host-up    # 인프라(DB 등) 실행
make host-be    # 백엔드 서버 실행
```

## 스크립트

| 명령어               | 설명                                   |
| -------------------- | -------------------------------------- |
| `npm install`        | 의존성 설치                            |
| `npm run dev`        | 개발 서버 실행 (http://localhost:3000) |
| `npm run build`      | 프로덕션 빌드                          |
| `npm run start`      | 프로덕션 서버 실행                     |
| `npm run lint`       | ESLint 검사                            |
| `npm run check-type` | 타입 검사                              |
| `npm run format`     | Prettier 포맷팅                        |
| `npm run openapi-ts` | OpenAPI 타입 생성                      |

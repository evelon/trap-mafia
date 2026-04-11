# Trap Mafia Frontend

실시간 멀티플레이어 마피아 게임의 프론트엔드. 게스트 인증 → 방 참가 → 게임 진행(밤/낮 투표) → 결과 흐름을 SSE 기반 실시간 통신으로 처리한다.

## 스택

- **프레임워크**: Next.js 16 (App Router) + React 19
- **언어**: TypeScript 5, ESM
- **스타일링**: Tailwind CSS 4
- **UI 컴포넌트**: shadcn/ui (Radix UI 기반), Lucide 아이콘, Sonner (토스트)
- **상태 관리**: TanStack React Query 5 (서버 상태)
- **폼**: React Hook Form + Zod 4

## 스크립트

| 명령어 | 설명 |
| --- | --- |
| `pnpm dev:https` | 개발 서버 실행 (`dev` 대신 이것을 사용) |
| `pnpm lint` | ESLint 검사 |
| `pnpm check-types` | 타입 검사 |
| `pnpm format` | Prettier 포맷팅 |
| `pnpm openapi-ts` | OpenAPI 타입 생성 |

## src 구조

```
src/
├── app/                    # App Router 라우트
├── client/                 # API 클라이언트 (자동 생성 코드 포함)
├── features/               # 피처별 컴포넌트 (layout 포함)
├── shadcn-ui/              # shadcn 컴포넌트, 훅, 유틸
├── shared/                 # 공통 유틸리티
└── middleware.ts            # 인증 기반 라우트 가드
```

- 경로 별칭: `@/*` → `./src/*`

## 피처 스펙

구현 설계는 `specs/` 디렉토리의 스펙 문서를 기준으로 한다.
스펙 목록은 `specs/README.md` 참조.

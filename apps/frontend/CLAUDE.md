# Trap Mafia Frontend

실시간 멀티플레이어 마피아 게임의 프론트엔드. 방 생성/참가 → 게임 진행(토론, 투표) 흐름을 SSE 기반 실시간 통신으로 처리한다.

## 스택

- **프레임워크**: Next.js 16 (App Router) + React 19
- **언어**: TypeScript 5, ESM
- **스타일링**: Tailwind CSS 4
- **UI 컴포넌트**: shadcn/ui (Radix UI 기반), Lucide 아이콘, Sonner (토스트)
- **상태 관리**: TanStack React Query 5 (서버 상태)
- **폼**: React Hook Form + Zod 4

## 주요 프로젝트 구조

```
src/
├── app/                    # App Router 라우트
├── features/               # 피처별 컴포넌트 (layout 포함)
├── shared/                 # 공통 유틸리티
├── shadcn-ui/              # shadcn 컴포넌트, 훅, 유틸
├── client/
│   └── gen/                # OpenAPI-TS 자동 생성 코드 (수동 편집 금지)
│       ├── types.gen.ts    # 타입 정의
│       ├── zod.gen.ts      # Zod 스키마
│       ├── sdk.gen.ts      # SDK (SSE용)
│       ├── @tanstack/      # React Query 훅 (REST용)
│       └── ...
└── ...
```

> 위 구조는 전체 목록이 아니며, 핵심만 의도적으로 축약해 표시한 것이다.

- 경로 별칭: `@/*` → `./src/*`

## 백엔드 연동

- 백엔드: `../apps/backend` (별도 프로젝트)
- 코드 생성: `pnpm openapi-ts` (설정: `openapi-ts.config.ts`)
- `src/client/gen/`은 자동 생성 코드이므로 직접 수정하지 않는다.
- REST API, SSE 연동 시 **반드시** `docs/rules/api-integration.md`를 참조한다

## 컨벤션

- 공통 UI 컴포넌트는 `src/shadcn-ui/ui`에 동일/유사 컴포넌트가 있는지 먼저 확인하고, 있으면 해당 컴포넌트를 우선 사용한다.

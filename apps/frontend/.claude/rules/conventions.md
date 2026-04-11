---
description: 프로젝트 고유 컨벤션 (컴포넌트 구조, export 규칙 등)
---

# 컨벤션

- 공통 UI 컴포넌트는 `src/shadcn-ui/ui`에 있는 것을 우선 사용한다.
- 컴포넌트의 prop 타입은 인라인으로 작성하지 않고, 별도로 분리해 작성한다.
- named export를 사용한다. (단, Next.js 컨벤션이 default export를 요구하는 파일은 예외.)

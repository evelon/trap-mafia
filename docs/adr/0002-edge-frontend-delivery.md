# ADR-0002: Edge Proxy & Frontend Delivery Strategy

## Status

Accepted

## Context

이 프로젝트는 웹 기반 게임 서비스로,  
SSE(Server-Sent Events) 및 WebSocket을 통한 **실시간 상태 전달**이 핵심 요구사항이다.

초기 운영 환경은 다음과 같은 제약을 가진다.

- 단일 서버에서 FE / BE / Edge Proxy를 함께 운영
- 동시 접속 목표는 약 20–100명 수준
- HTTPS 설정, 라우팅, 프록시 동작은 최대한 단순해야 함
- 프론트엔드는 “로그인 / 방 선택 / 게임 화면”으로 역할이 명확히 분리됨

이 단계에서 해결하려는 핵심 문제는 다음과 같다.

- SSE/WS를 안정적으로 전달할 수 있는 Edge Proxy 선택
- 프론트엔드 배포 방식을 단순화하여 운영 복잡도 감소
- 초기 운영에서 불필요한 런타임(Node 등)을 제거

## Scope & Non-Goals

- 이 ADR은 **Edge Proxy 선택과 Frontend 전달 방식**만을 다룬다.
- Backend 프레임워크 및 데이터 계층 선택은 다루지 않는다.
- CDN, 멀티 리전, 고급 캐싱 전략은 현 단계의 목표가 아니다.

## Decision

다음과 같은 구조를 채택한다.

- Edge Proxy로 **Caddy**를 사용한다.
- 프론트엔드는 **Next.js 기반 정적 파일 생성(static export)** 방식으로 배포한다.
- 운영 환경에서 Node.js 런타임을 사용하지 않는다.
- Caddy는 다음 역할을 담당한다.
  - HTTPS(TLS) 처리
  - 정적 파일 서빙
  - `/api`, `/sse` 요청에 대한 Backend reverse proxy

## Options Considered

### Option A: Nginx + Dynamic Next.js (Node Runtime)

- 장점
  - 널리 사용되는 전통적인 구성
  - 풍부한 레퍼런스
- 단점
  - HTTPS 설정 및 인증서 관리가 번거로움
  - Node 런타임을 운영 환경에 포함해야 함
  - SSE/WS 설정 시 세부 튜닝 부담

### Option B: Caddy + Static Frontend (Selected)

- 장점
  - HTTPS 설정을 자동화하여 운영 부담 감소
  - 설정 문법이 간결하고 SSE/WS와의 연결성이 좋음
  - 정적 파일 서빙으로 프론트엔드 운영 복잡도 최소화
- 단점
  - Nginx 대비 레퍼런스가 상대적으로 적음
  - 정적 배포로 인해 일부 동적 렌더링 기능 사용 불가

## Rationale

초기 단계에서 Edge Proxy의 가장 중요한 역할은  
**HTTPS 처리와 안정적인 실시간 연결 전달(SSE/WS)**이다.

Caddy는 HTTPS 인증서 발급 및 갱신을 자동으로 처리하여,  
Nginx 사용 시 가장 번거롭다고 느꼈던 SSL 설정 문제를 제거해 준다.

프론트엔드는 Next.js를 사용하되,  
이 프로젝트에서는 로그인 화면 / 방 선택 / 게임 화면 등 역할이 명확하여  
**완전 정적(static export) 배포로도 충분하다고 판단했다.**

이를 통해 다음 이점을 얻는다.

- 운영 환경에서 Node.js 런타임 제거
- Edge Proxy와 Frontend의 역할을 명확히 분리
- 배포 구조 단순화 및 자원 사용 최소화

동적 렌더링이 필요한 요구사항이 생길 경우,  
그때 다시 Frontend 전달 방식을 재검토할 수 있도록 여지를 남긴다.

## Consequences

### Positive

- HTTPS 설정 및 운영 복잡도 감소
- SSE/WS 전달에 유리한 Edge 구성
- Frontend 배포 및 롤백 단순화
- 운영 자원 사용 최소화

### Negative / Risks

- 정적 배포로 인해 일부 동적 기능 제약
- Caddy 사용 경험이 적은 팀원에게는 초기 학습 비용 발생

### Mitigations

- 프론트엔드 요구사항이 변경될 경우 Next.js 전달 전략 재검토
- Edge Proxy 설정을 ADR 및 문서로 명확히 기록

## Rollout / Next Steps

- Caddyfile(local/host) 기본 구성 확정
- 정적 Frontend 빌드 산출물 구조 확정
- Backend 플랫폼 및 데이터 계층 선택을 ADR-0003으로 분리하여 결정

---

Last updated: 2026-01-29

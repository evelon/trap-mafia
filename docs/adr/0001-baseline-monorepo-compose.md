# ADR-0001: Monorepo + Docker Compose Baseline Architecture

## Status

Accepted

## Context

이 프로젝트는 소규모 웹 기반 게임 서비스로, 초기 동시 접속 목표는 약 20–100명 수준이다.  
초기 단계에서는 기능 구현과 반복적인 실험 속도가 가장 중요하며, 과도한 인프라 복잡도는 피하고자 한다.

운영 환경은 다음과 같은 전제를 가진다.

- FE, BE, Edge Proxy, DB, Cache 모두 **단일 서버**에서 시작
- 로컬 개발 환경과 운영 환경의 차이를 최소화
- 배포 및 롤백이 단순하고 예측 가능해야 함
- 추후 트래픽 증가 시 **점진적인 확장 경로**를 가질 것

이 단계에서 해결하려는 핵심 문제는 다음과 같다.

- FE/BE/인프라 변경을 빠르게 묶어서 배포할 수 있는 구조
- 로컬에서 재현 가능한 운영 환경
- “지금은 작지만, 나중에 분리 가능한” 아키텍처

## Scope & Non-Goals

- 이 ADR은 **레포지토리 구조와 배포 베이스라인**만을 다룬다.
- Edge Proxy, Backend, Frontend, Data Store의 **구체적인 기술 선택**은 다루지 않는다.
- 고가용성, 자동 스케일링, 멀티 리전 구성은 현 단계의 목표가 아니다.

## Decision

다음과 같은 베이스라인 아키텍처를 채택한다.

- **단일 Monorepo**에 FE / BE / Edge Proxy / DB / Cache / 배포 설정을 함께 관리
- 서비스 기동 및 연동은 **Docker Compose**를 표준으로 사용
- 초기 운영은 **단일 서버 + Compose** 기반으로 수행

구체적인 기술 선택(Edge Proxy, BE/FE 프레임워크 등)은 별도의 ADR에서 다룬다.

## Options Considered

### Option A: Multiple Repositories (FE / BE / Infra 분리)

- 장점
  - 독립적인 릴리즈 및 권한 분리
  - 대규모 조직에 적합
- 단점
  - 초기 단계에서 변경/배포 조율 비용이 큼
  - 로컬 환경 구성과 운영 환경 재현이 어려움

### Option B: Monorepo + Docker Compose

- 장점
  - 한 번의 변경으로 전체 스택을 일관되게 수정 가능
  - 로컬과 운영 환경의 높은 유사성
  - 배포 및 디버깅 흐름 단순화
- 단점
  - 레포지토리 크기 증가
  - CI/CD 분리 관리가 어려울 수 있음

## Rationale

이 프로젝트는 초기 규모가 작고, FE/BE/인프라 변경이 동시에 발생하는 경우가 많다  
(예: 라우팅, 인증 흐름, 프록시 설정, SSE 엔드포인트 등).

따라서 레포지토리 분리에 따른 관리 비용보다,  
**통합 관리로 얻는 개발 속도와 운영 단순성**이 더 큰 가치라고 판단했다.

Docker Compose는 단일 서버 운영에서 다음 장점을 제공한다.

- 서비스 간 의존성, 네트워크, 환경 변수를 코드로 명시 가능
- 로컬에서도 운영과 거의 동일한 환경 재현
- 배포 시 “이미 검증된 구성”을 그대로 사용 가능

초기 단계에서 Kubernetes와 같은 오케스트레이션 도구는  
운영 복잡도 대비 얻는 이점이 제한적이므로 채택하지 않는다.

## Consequences

### Positive

- 빠른 개발 및 배포 사이클
- 로컬/운영 환경 불일치로 인한 오류 감소
- 인프라 변경을 포함한 기능 단위 PR 작성 가능

### Negative / Risks

- 레포지토리가 커질 수 있음
- FE/BE 변경이 서로 영향을 줄 가능성
- Compose 기반 구조는 대규모 수평 확장에 한계가 있음

### Mitigations

- 디렉토리 구조를 명확히 분리 (apps/fe, apps/be, infra 등)
- CI/CD에서 서비스 단위(targeted) 빌드/배포 전략 사용
- 핵심 상태는 DB를 SSOT로 두고, 서비스 분리는 단계적으로 진행

## Rollout / Next Steps

- Monorepo 디렉토리 구조 확정
- Docker Compose(local/prod) 기본 구성 작성
- Edge Proxy / Backend / Frontend 선택을 개별 ADR로 분리하여 결정

---

Last updated: 2026-01-29

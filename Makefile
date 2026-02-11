# Makefile
# Repo root 기준:
# - apps/backend, apps/frontend
# - ops/compose/host/compose.yml, ops/compose/local/compose.yml
# - ops/env/{compose, runtime}.{host,local}.env


SHELL := /bin/bash

# Makefile이 있는 레포 루트 절대경로 (trailing slash 포함)
ROOT_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

# ---- project ----
PROJECT := trap-mafia-v4

# ---- paths ----
BE_DIR := apps/backend
FE_DIR := apps/frontend

COMPOSE_HOST_FILE := $(ROOT_DIR)ops/compose/host/compose.yml
COMPOSE_LOCAL_FILE := $(ROOT_DIR)ops/compose/local/compose.yml

ENV_COMPOSE_HOST := $(ROOT_DIR)ops/env/compose.host.env
ENV_COMPOSE_LOCAL := $(ROOT_DIR)ops/env/compose.local.env

ENV_RUNTIME_HOST := $(ROOT_DIR)ops/env/runtime.host.env
ENV_RUNTIME_LOCAL := $(ROOT_DIR)ops/env/runtime.local.env

# ---- helpers ----
define RUN_WITH_ENV
set -euo pipefail; \
set -a; \
source "$(1)"; \
set +a; \
$(2)
endef

define DC
COMPOSE_PROJECT_NAME="$(PROJECT)" docker compose --env-file "$(1)" -f "$(2)"
endef

.PHONY: help \
  deps deps-be deps-fe \
  host-up host-up-only host-app-up host-down host-restart host-ps host-logs \
  host-be host-fe \
  host-migrate host-migrate-only \
  local-up local-up-only local-down local-restart local-ps local-logs \
  local-infra-up local-infra-up-only local-infra-down local-infra-logs \
  local-be local-fe \
  local-migrate local-migrate-only \
  clean

help:
	@echo "Core:"
	@echo "  deps                    # uv sync + pnpm install (C 정책이지만 up에서 기본 호출)"
	@echo ""
	@echo "Host (dev default):"
	@echo "  host-up                 # deps + infra up + migrate + (BE/FE 동시 실행)"
	@echo "  host-up-only            # infra up only (deps/migrate 없음)"
	@echo "  host-migrate            # deps-be + migrate"
	@echo "  host-migrate-only       # migrate only (deps-be 없음)"
	@echo "  host-be                 # backend 로컬 실행 (runtime.host.env 주입)"
	@echo "  host-fe                 # frontend 로컬 실행 (runtime.host.env 주입)"
	@echo "  host-logs               # 인프라 로그 tail"
	@echo ""
	@echo "Local (final verify one-shot):"
	@echo "  local-up                # deps + infra up + migrate + (BE/FE 동시 실행)"
	@echo "  local-up-only            # infra up + migrate + (BE/FE 동시 실행)  (deps 없음)"
	@echo "  local-infra-up           # deps + infra up + migrate"
	@echo "  local-infra-up-only      # infra up only"
	@echo "  local-migrate            # deps-be + migrate"
	@echo "  local-migrate-only       # migrate only (deps-be 없음)"
	@echo ""
	@echo "Compose project name: $(PROJECT)"

# -------------------------
# deps
# -------------------------
deps: deps-be deps-fe

deps-be:
	@echo "[deps-be] uv sync in $(BE_DIR)"
	cd "$(BE_DIR)" && uv sync

deps-fe:
	@echo "[deps-fe] pnpm install in $(FE_DIR)"
	cd "$(FE_DIR)" && pnpm install --frozen-lockfile

# -------------------------
# migrations (alembic)
# -------------------------
# NOTE: migration 명령은 프로젝트에 맞게 여기만 바꾸면 됨.
# 기본은 alembic upgrade head 로 둠.
host-migrate: deps-be host-migrate-only
host-migrate-only:
	@echo "[host-migrate] alembic upgrade head (runtime host env)"
	@cd "$(BE_DIR)" && $(call RUN_WITH_ENV,$(ENV_RUNTIME_HOST),uv run alembic upgrade head)

local-migrate: deps-be local-migrate-only
local-migrate-only:
	@echo "[local-migrate] alembic upgrade head (runtime local env)"
	@cd "$(BE_DIR)" && $(call RUN_WITH_ENV,$(ENV_RUNTIME_LOCAL),uv run alembic upgrade head)

# -------------------------
# host mode
# - infra: compose host
# - apps: local process
# -------------------------
# host-up: deps 포함 + infra up + migrate + BE/FE 동시 실행
host-up: deps host-up-only host-migrate-only host-app-up

host-up-only:
	@echo "[host-up-only] infra up (compose host)"
	@$(call DC,$(ENV_COMPOSE_HOST),$(COMPOSE_HOST_FILE)) up -d

host-down:
	@echo "[host-down] infra down (compose host)"
	@$(call DC,$(ENV_COMPOSE_HOST),$(COMPOSE_HOST_FILE)) down

host-restart:
	@echo "[host-restart] infra restart (compose host)"
	@$(call DC,$(ENV_COMPOSE_HOST),$(COMPOSE_HOST_FILE)) restart

host-ps:
	@$(call DC,$(ENV_COMPOSE_HOST),$(COMPOSE_HOST_FILE)) ps

# host는 A: 인프라 로그만 tail
host-logs:
	@echo "[host-logs] infra logs -f (compose host)"
	@$(call DC,$(ENV_COMPOSE_HOST),$(COMPOSE_HOST_FILE)) logs -f --tail=200

host-be:
	@echo "[host-be] run backend with $(ENV_RUNTIME_HOST)"
	@cd "$(BE_DIR)" && $(call RUN_WITH_ENV,$(ENV_RUNTIME_HOST),uv run uvicorn main:app --reload --port 8000)

host-fe:
	@echo "[host-fe] run frontend with $(ENV_RUNTIME_HOST)"
	@cd "$(FE_DIR)" && $(call RUN_WITH_ENV,$(ENV_RUNTIME_HOST),pnpm dev)


# -------------------------
# local mode
# - infra: compose local
# - one-shot: infra + backend + frontend
# -------------------------
local-infra-up: deps local-infra-up-only local-migrate-only

local-infra-up-only:
	@echo "[local-infra-up-only] infra up (compose local)"
	@$(call DC,$(ENV_COMPOSE_LOCAL),$(COMPOSE_LOCAL_FILE)) up -d

local-infra-down:
	@echo "[local-infra-down] infra down (compose local)"
	@$(call DC,$(ENV_COMPOSE_LOCAL),$(COMPOSE_LOCAL_FILE)) down

local-infra-logs:
	@echo "[local-infra-logs] infra logs -f (compose local)"
	@$(call DC,$(ENV_COMPOSE_LOCAL),$(COMPOSE_LOCAL_FILE)) logs -f --tail=200

local-ps:
	@$(call DC,$(ENV_COMPOSE_LOCAL),$(COMPOSE_LOCAL_FILE)) ps

local-restart:
	@echo "[local-restart] infra restart (compose local)"
	@$(call DC,$(ENV_COMPOSE_LOCAL),$(COMPOSE_LOCAL_FILE)) restart

# local-up: deps 포함 + 한 방 실행
local-up: deps local-up-only

# local-up-only: deps 제외 + 인프라/마이그 + BE/FE 동시 실행
local-up-only: local-infra-up-only local-migrate-only
	@echo "[local-up] one-shot: infra + migrate + backend + frontend"
	@echo "  - stop: Ctrl+C"
	@set -euo pipefail; \
	trap 'echo; echo "[local-up] stopping..."; kill 0' INT TERM; \
	( cd "$(BE_DIR)" && $(call RUN_WITH_ENV,$(ENV_RUNTIME_LOCAL),uv run uvicorn main:app --reload --port 8000) ) & \
	( cd "$(FE_DIR)" && $(call RUN_WITH_ENV,$(ENV_RUNTIME_LOCAL),pnpm dev) ) & \
	wait

local-down: local-infra-down

# local은 B를 원했지만, make가 전체 로그를 '통합 tail' 하긴 애매해서
# local-up에서 BE/FE 로그가 이미 터미널에 나오므로 local-logs는 인프라만 제공.
# (원하면 나중에 concurrently/foreman/tmux 방식으로 "전체 logs" 타겟 추가 가능)
local-logs: local-infra-logs

clean:
	@echo "[clean] (noop) 필요한 경우 여기에 캐시/볼륨 정리 타겟 추가"

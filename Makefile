# Root orchestration: backend/ and frontend/ have their own Compose files and Makefiles.
# Run from the repository root. Requires Docker Compose v2.

BACKEND_DC = docker compose -f backend/docker_compose/app.dev.yaml -f backend/docker_compose/kafka.yaml --env-file backend/.env
BACKEND_DC_MODEL = docker compose -f backend/docker_compose/app.dev.yaml -f backend/docker_compose/kafka.yaml -f backend/docker_compose/model-service.yaml --env-file backend/.env
FRONTEND_DC = docker compose -f frontend/docker-compose.yaml --project-directory frontend

.PHONY: help
help:
	@echo "Alpaca Astro Center — root Makefile"
	@echo ""
	@echo "  Up / down (full stack: API+Kafka + UI)"
	@echo "    make dev              — backend + frontend containers"
	@echo "    make dev-down         — stop frontend, then backend+Kafka"
	@echo "    make up | make down   — aliases for dev / dev-down"
	@echo ""
	@echo "  With model-service"
	@echo "    make dev-with-model"
	@echo "    make dev-with-model-down"
	@echo ""
	@echo "  Up / down partial"
	@echo "    make up-backend | down-backend"
	@echo "    make up-frontend | down-frontend"
	@echo ""
	@echo "  Logs (follow; Ctrl+C stops)"
	@echo "    make logs             — backend (main-app+kafka) + frontend (interleaved)"
	@echo "    make logs-backend     — backend+Kafka only"
	@echo "    make logs-frontend    — UI nginx only"
	@echo "    make logs-with-model  — backend+Kafka+model + frontend (if model stack is up)"
	@echo ""
	@echo "  Status"
	@echo "    make ps               — docker compose ps for both stacks"

.PHONY: dev
dev:
	$(MAKE) -C backend app-dev
	$(MAKE) -C frontend up

.PHONY: dev-down
dev-down:
	$(MAKE) -C frontend down
	$(MAKE) -C backend down-dev

.PHONY: dev-with-model
dev-with-model:
	$(MAKE) -C backend app-dev-with-model
	$(MAKE) -C frontend up

.PHONY: dev-with-model-down
dev-with-model-down:
	$(MAKE) -C frontend down
	$(MAKE) -C backend down-dev-with-model

.PHONY: up
up: dev

.PHONY: down
down: dev-down

.PHONY: up-backend
up-backend:
	$(MAKE) -C backend app-dev

.PHONY: up-frontend
up-frontend:
	$(MAKE) -C frontend up

.PHONY: down-backend
down-backend:
	$(MAKE) -C backend down-dev

.PHONY: down-frontend
down-frontend:
	$(MAKE) -C frontend down

.PHONY: logs
logs:
	@echo "Streaming backend (main-app + kafka) and frontend; Ctrl+C to stop."
	@sh -c 'set -e; $(BACKEND_DC) logs -f & $(FRONTEND_DC) logs -f & wait'

.PHONY: logs-backend
logs-backend:
	$(MAKE) -C backend app-dev-logs

.PHONY: logs-frontend
logs-frontend:
	$(MAKE) -C frontend logs

.PHONY: logs-with-model
logs-with-model:
	@echo "Streaming backend+Kafka+model and frontend; Ctrl+C to stop."
	@sh -c 'set -e; $(BACKEND_DC_MODEL) logs -f & $(FRONTEND_DC) logs -f & wait'

.PHONY: ps
ps:
	@echo "=== backend (main-app + kafka) ==="
	@$(BACKEND_DC) ps -a
	@echo ""
	@echo "=== frontend ==="
	@$(FRONTEND_DC) ps -a

.PHONY: ps-with-model
ps-with-model:
	@echo "=== backend (main-app + kafka + model-service) ==="
	@$(BACKEND_DC_MODEL) ps -a
	@echo ""
	@echo "=== frontend ==="
	@$(FRONTEND_DC) ps -a

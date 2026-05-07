DC = docker compose
APP = docker_compose/app.yaml
APP_DEV = docker_compose/app.dev.yaml
KAFKA = docker_compose/kafka.yaml
MONGO = docker_compose/mongo.yaml
MONGO_EXPRESS = docker_compose/mongo-express.yaml
MODEL_SERVICE = docker_compose/model-service.yaml
APP_SERVICE = main-app
ENV = --env-file .env
PYTHON_IMAGE = python:3.12-slim-bookworm
NEWMAN_IMAGE = postman/newman:alpine
HOST_UID = $(shell id -u)
HOST_GID = $(shell id -g)
HARDWARE_SMOKE_REPORT = artifacts/hardware-smoke-dry-run.json
HARDWARE_VALIDATION_REPORT = artifacts/hardware-validation-dry-run.json
HARDWARE_SMOKE_NOTES = artifacts/hardware-smoke-dry-run.md
HARDWARE_VALIDATION_NOTES = artifacts/hardware-validation-dry-run.md
HARDWARE_SMOKE_LIVE_REPORT = artifacts/hardware-smoke-live-run.json
HARDWARE_SMOKE_LIVE_NOTES = artifacts/hardware-smoke-live-run.md
HARDWARE_ARTIFACT_DIR = artifacts

.PHONY: app-dev
app-dev:
	${DC} -f ${APP_DEV} -f ${KAFKA} ${ENV} up --build -d

.PHONY: app-dev-with-model
app-dev-with-model:
	${DC} -f ${APP_DEV} -f ${KAFKA} -f ${MODEL_SERVICE} ${ENV} up --build -d

.PHONY: app-dev-logs
app-dev-logs:
	${DC} -f ${APP_DEV} logs -f

.PHONY: app-dev-with-model-logs
app-dev-with-model-logs:
	${DC} -f ${APP_DEV} -f ${KAFKA} -f ${MODEL_SERVICE} logs -f

.PHONY: storages
storages:
	${DC} -f ${MONGO} ${ENV} up -d --build

.PHONY: down-dev
down-dev:
	${DC} -f ${APP_DEV} -f ${KAFKA} ${ENV} down

.PHONY: down-dev-with-model
down-dev-with-model:
	${DC} -f ${APP_DEV} -f ${KAFKA} -f ${MODEL_SERVICE} ${ENV} down

.PHONY: down
down:
	${DC} -f ${APP} -f ${APP_DEV} -f ${KAFKA} -f ${MONGO} -f ${MONGO_EXPRESS} -f ${MODEL_SERVICE} ${ENV} down

.PHONY: ui
ui:
	${DC} -f ${MONGO_EXPRESS} ${ENV} up --build -d

.PHONY: purge
purge:
	${DC} -f ${KAFKA} -f ${MONGO} -f ${MONGO_EXPRESS} ${ENV} down -v

.PHONY: shell
shell:
	${DC} -f ${APP} exec -it ${APP_SERVICE} bash

.PHONY: test
test:
	${DC} -f ${APP_DEV} exec ${APP_SERVICE} pytest -q

.PHONY: test-all
test-all:
	${DC} -f ${APP_DEV} exec ${APP_SERVICE} pytest -q

.PHONY: test-unit
test-unit:
	${DC} -f ${APP_DEV} exec ${APP_SERVICE} pytest -q tests/unit

.PHONY: test-integration
test-integration:
	${DC} -f ${APP_DEV} exec ${APP_SERVICE} pytest -q tests/integration

.PHONY: test-local
test-local:
	docker run --rm -v ${PWD}:/workspace -w /workspace ${PYTHON_IMAGE} bash -lc "pip install -q poetry==1.8.2 && poetry install -q --no-interaction && poetry run pytest -q"

.PHONY: test-unit-local
test-unit-local:
	docker run --rm -v ${PWD}:/workspace -w /workspace ${PYTHON_IMAGE} bash -lc "pip install -q poetry==1.8.2 && poetry install -q --no-interaction && poetry run pytest -q tests/unit"

.PHONY: test-integration-local
test-integration-local:
	docker run --rm -v ${PWD}:/workspace -w /workspace ${PYTHON_IMAGE} bash -lc "pip install -q poetry==1.8.2 && poetry install -q --no-interaction && poetry run pytest -q tests/integration"

.PHONY: postman-smoke-local
postman-smoke-local:
	docker run --rm --network host -v ${PWD}/postman:/etc/newman ${NEWMAN_IMAGE} run /etc/newman/alpaca-astro-center.smoke.postman_collection.json -e /etc/newman/alpaca-astro-center.local.postman_environment.json --env-var base_url=$${BASE_URL:-http://127.0.0.1:8000}

.PHONY: postman-smoke-up
postman-smoke-up:
	${DC} -f ${APP_DEV} -f ${KAFKA} -f ${MODEL_SERVICE} ${ENV} up --build -d && ${MAKE} postman-smoke-local

.PHONY: postman-smoke-up-clean
postman-smoke-up-clean:
	${DC} -f ${APP_DEV} -f ${KAFKA} -f ${MODEL_SERVICE} ${ENV} up --build -d && ${MAKE} postman-smoke-local && ${MAKE} down-dev-with-model

.PHONY: hardware-smoke-dry-run
hardware-smoke-dry-run:
	docker run --rm -v ${PWD}:/workspace -w /workspace ${PYTHON_IMAGE} sh -lc "mkdir -p ${HARDWARE_ARTIFACT_DIR} && chown -R ${HOST_UID}:${HOST_GID} ${HARDWARE_ARTIFACT_DIR} && rm -f ${HARDWARE_SMOKE_REPORT}" && \
	docker run --rm --network host --user ${HOST_UID}:${HOST_GID} -v ${PWD}:/workspace -w /workspace ${PYTHON_IMAGE} python scripts/hardware_smoke_runner.py --base-url $${BASE_URL:-http://127.0.0.1:8000} --strict

.PHONY: hardware-validation-dry-run
hardware-validation-dry-run:
	docker run --rm -v ${PWD}:/workspace -w /workspace ${PYTHON_IMAGE} sh -lc "mkdir -p ${HARDWARE_ARTIFACT_DIR} && chown -R ${HOST_UID}:${HOST_GID} ${HARDWARE_ARTIFACT_DIR} && rm -f ${HARDWARE_VALIDATION_REPORT}" && \
	docker run --rm --network host --user ${HOST_UID}:${HOST_GID} -v ${PWD}:/workspace -w /workspace ${PYTHON_IMAGE} python scripts/hardware_smoke_runner.py --base-url $${BASE_URL:-http://127.0.0.1:8000} --validation-only --report-path ${HARDWARE_VALIDATION_REPORT} --strict

.PHONY: hardware-smoke-dry-run-with-notes
hardware-smoke-dry-run-with-notes:
	docker run --rm -v ${PWD}:/workspace -w /workspace ${PYTHON_IMAGE} sh -lc "mkdir -p ${HARDWARE_ARTIFACT_DIR} && chown -R ${HOST_UID}:${HOST_GID} ${HARDWARE_ARTIFACT_DIR} && rm -f ${HARDWARE_SMOKE_REPORT} ${HARDWARE_SMOKE_NOTES}" && \
	docker run --rm --network host --user ${HOST_UID}:${HOST_GID} -v ${PWD}:/workspace -w /workspace ${PYTHON_IMAGE} python scripts/hardware_smoke_runner.py --base-url $${BASE_URL:-http://127.0.0.1:8000} --report-path ${HARDWARE_SMOKE_REPORT} --notes-path ${HARDWARE_SMOKE_NOTES} --strict

.PHONY: hardware-validation-dry-run-with-notes
hardware-validation-dry-run-with-notes:
	docker run --rm -v ${PWD}:/workspace -w /workspace ${PYTHON_IMAGE} sh -lc "mkdir -p ${HARDWARE_ARTIFACT_DIR} && chown -R ${HOST_UID}:${HOST_GID} ${HARDWARE_ARTIFACT_DIR} && rm -f ${HARDWARE_VALIDATION_REPORT} ${HARDWARE_VALIDATION_NOTES}" && \
	docker run --rm --network host --user ${HOST_UID}:${HOST_GID} -v ${PWD}:/workspace -w /workspace ${PYTHON_IMAGE} python scripts/hardware_smoke_runner.py --base-url $${BASE_URL:-http://127.0.0.1:8000} --validation-only --report-path ${HARDWARE_VALIDATION_REPORT} --notes-path ${HARDWARE_VALIDATION_NOTES} --strict

.PHONY: hardware-preflight-dry-run-with-notes
hardware-preflight-dry-run-with-notes: hardware-smoke-dry-run-with-notes hardware-validation-dry-run-with-notes

.PHONY: hardware-preflight-dry-run
hardware-preflight-dry-run: hardware-smoke-dry-run hardware-validation-dry-run

.PHONY: hardware-smoke-live-run
hardware-smoke-live-run:
	docker run --rm -v ${PWD}:/workspace -w /workspace ${PYTHON_IMAGE} sh -lc "mkdir -p ${HARDWARE_ARTIFACT_DIR} && chown -R ${HOST_UID}:${HOST_GID} ${HARDWARE_ARTIFACT_DIR} && rm -f ${HARDWARE_SMOKE_LIVE_REPORT} ${HARDWARE_SMOKE_LIVE_NOTES}" && \
	docker run --rm --network host --user ${HOST_UID}:${HOST_GID} -v ${PWD}:/workspace -w /workspace ${PYTHON_IMAGE} python scripts/hardware_smoke_runner.py --base-url $${BASE_URL:-http://127.0.0.1:8000} --include-commands --allow-command-checks-when-not-ready --command-token "$${COMMAND_TOKEN:-}" --report-path ${HARDWARE_SMOKE_LIVE_REPORT} --notes-path ${HARDWARE_SMOKE_LIVE_NOTES} --strict

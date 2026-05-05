DC = docker compose
APP = docker_compose/app.yaml
APP_DEV = docker_compose/app.dev.yaml
KAFKA = docker_compose/kafka.yaml
MONGO = docker_compose/mongo.yaml
MONGO_EXPRESS = docker_compose/mongo-express.yaml
APP_SERVICE = main-app
ENV = --env-file .env
PYTHON_IMAGE = python:3.12-slim-bookworm

.PHONY: app-dev
app-dev:
	${DC} -f ${APP_DEV} -f ${KAFKA} ${ENV} up --build -d

.PHONY: app-dev-logs
app-dev-logs:
	${DC} -f ${APP_DEV} logs -f

.PHONY: storages
storages:
	${DC} -f ${MONGO} ${ENV} up -d --build

.PHONY: down-dev
down-dev:
	${DC} -f ${APP_DEV} -f ${KAFKA} ${ENV} down

.PHONY: down
down:
	${DC} -f ${APP} -f ${APP_DEV} -f ${KAFKA} -f ${MONGO} -f ${MONGO_EXPRESS} ${ENV} down

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

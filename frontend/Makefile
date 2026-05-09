DC = docker compose
COMPOSE = docker-compose.yaml

.PHONY: up
up:
	${DC} -f ${COMPOSE} up --build -d

.PHONY: down
down:
	${DC} -f ${COMPOSE} down

.PHONY: logs
logs:
	${DC} -f ${COMPOSE} logs -f

.PHONY: build
build:
	${DC} -f ${COMPOSE} build

.PHONY: install
install:
	npm install

.PHONY: dev
dev:
	npm run dev

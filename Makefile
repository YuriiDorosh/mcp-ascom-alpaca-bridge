# Orchestration: backend and frontend have their own Makefiles and Compose files.

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

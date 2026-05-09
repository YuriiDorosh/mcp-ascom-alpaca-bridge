PYTHON_IMAGE = python:3.12-slim-bookworm

.PHONY: test-local
test-local:
	docker run --rm -v ${PWD}:/workspace -w /workspace ${PYTHON_IMAGE} bash -lc "pip install -q poetry==1.8.2 && poetry install -q --no-interaction && poetry run pytest -q"

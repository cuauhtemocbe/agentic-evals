.DEFAULT_GOAL := help
.PHONY: help build up up-d down logs test coverage-xml test-v lint format-check typecheck lock-check install-hooks install notebook-local test-local lint-local notebook

# --- Docker (flujo principal) ---

build: ## Construir la imagen de desarrollo
	docker compose build

up: ## Levantar el servicio en foreground (con logs)
	docker compose up

up-d: ## Levantar el servicio en background, esperando a que esté healthy
	docker compose up -d --wait

down: ## Bajar el servicio
	docker compose down

logs: ## Seguir los logs del servicio api
	docker compose logs -f api

test: up-d ## Correr la suite de tests con cobertura dentro de Docker
	docker compose exec api pytest docs --cov=docs --cov-report=term-missing

coverage-xml: up-d ## Generar coverage.xml dentro de Docker y copiarlo al host (para SonarQube)
	docker compose exec api pytest docs --cov=docs --cov-report=xml:coverage.xml
	docker compose cp api:/app/coverage.xml ./coverage.xml

test-v: up-d ## Correr los tests en modo verbose dentro de Docker
	docker compose exec api pytest docs -v

lint: up-d ## Correr ruff check dentro de Docker
	docker compose exec api ruff check docs/

format-check: up-d ## Verificar formato con ruff dentro de Docker (sin modificar archivos)
	docker compose exec api ruff format --check docs/

typecheck: up-d ## Correr mypy dentro de Docker
	docker compose exec api mypy docs/

lock-check: up-d ## Verificar que poetry.lock esté sincronizado con pyproject.toml
	docker compose exec api poetry check --lock

notebook: up-d ## Levantar JupyterLab dentro de Docker (http://localhost:8888), notebooks en docs/
	docker compose exec api jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --notebook-dir=/app/docs --ServerApp.token='' --ServerApp.password='' --ServerApp.disable_check_xsrf=True

install-hooks: ## Habilitar el git hook de pre-commit (lint + format, corre en Docker)
	git config core.hooksPath .githooks
	chmod +x .githooks/pre-commit

# --- Local (opcional: fallback sin Docker, requiere Python 3.13 y Poetry) ---

install: ## [local] Instalar dependencias con poetry
	poetry install

notebook-local: ## [local] Levantar JupyterLab con poetry, notebooks en docs/
	poetry run jupyter lab --notebook-dir=docs --ServerApp.token='' --ServerApp.password='' --ServerApp.disable_check_xsrf=True

test-local: ## [local] Correr tests con poetry
	poetry run pytest docs -v

lint-local: ## [local] Correr ruff check con poetry
	poetry run ruff check docs/

help: ## Mostrar esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

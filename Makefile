.DEFAULT_GOAL := help
.PHONY: help build up up-d down logs test coverage-xml test-v lint format-check typecheck lock-check install-hooks install notebook-local test-local lint-local notebook streamlit-p1 streamlit-p1-local streamlit-m02-p2 streamlit-m02-p2-local streamlit-m03-p3 streamlit-m03-p3-local

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

streamlit-p1: up-d ## Levantar la app Streamlit de Proyecto_01 (Modulo 01) en Docker (http://localhost:8501)
	docker compose exec api streamlit run "docs/Modulo 01/Proyecto_01/app.py" --server.address=0.0.0.0 --server.port=8501

streamlit-m03-p3: up-d ## Levantar la app Streamlit de Proyecto_3 (Modulo 03) en Docker (http://localhost:8503)
	docker compose exec api streamlit run "docs/Modulo 03/Proyecto_3/app.py" --server.address=0.0.0.0 --server.port=8503

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

streamlit-p1-local: ## [local] Levantar la app Streamlit de Proyecto_01 (Modulo 01) con poetry
	poetry run streamlit run "docs/Modulo 01/Proyecto_01/app.py"

streamlit-m02-p2: up-d ## Levantar la app Streamlit de Proyecto_02 (Modulo 02) en Docker (http://localhost:8502)
	docker compose exec api streamlit run "docs/Modulo 02/Proyecto_02/src/app.py" --server.address=0.0.0.0 --server.port=8502

streamlit-m02-p2-local: ## [local] Levantar la app Streamlit de Proyecto_02 (Modulo 02) con poetry
	poetry run streamlit run "docs/Modulo 02/Proyecto_02/src/app.py" --server.port=8502

streamlit-m03-p3-local: ## [local] Levantar la app Streamlit de Proyecto_3 (Modulo 03) con poetry
	poetry run streamlit run "docs/Modulo 03/Proyecto_3/app.py" --server.port=8503

help: ## Mostrar esta ayuda
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-24s\033[0m %s\n", $$1, $$2}'

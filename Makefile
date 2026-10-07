SHELL := /bin/bash
.DEFAULT_GOAL := help
.PHONY: help infra infra-down dev front prod prod-down prod-logs lint fmt typecheck test migration migrate gen build \
	build-backend build-web

COMPOSE_DEV := docker compose -f docker-compose.yml -f docker-compose.dev.yml
COMPOSE_PROD := docker compose -p club110-prod
UV := cd backend && DB_HOST=localhost REDIS_HOST=localhost uv run --env-file ../.env

help:
	@echo "dev         infra in docker + backend on the host (debugger, fast restart)"
	@echo "front       admin panel dev server on http://localhost:5173 (run next to make dev)"
	@echo "prod        full stack in docker exactly as on the server (own containers and volumes)"
	@echo "prod-down   stop the prod stack"
	@echo "prod-logs   follow backend logs of the prod stack"
	@echo "infra       start postgres, redis, postgres-test in docker"
	@echo "infra-down  stop dev infra"
	@echo "lint        backend: ruff + pyright; frontend: eslint + prettier + tsc"
	@echo "fmt         format backend and frontend"
	@echo "test        backend pytest against postgres-test + frontend vitest"
	@echo "gen         regenerate the frontend API client from the backend OpenAPI schema"
	@echo "migration   autogenerate alembic revision: make migration m=\"add lessons\""
	@echo "migrate     alembic upgrade head on the dev database"
	@echo "build       build docker images club110-backend:latest and club110-web:latest"

infra:
	$(COMPOSE_PROD) down
	$(COMPOSE_DEV) up -d --wait postgres redis postgres-test

infra-down:
	$(COMPOSE_DEV) down

# One bot token allows a single getUpdates consumer, so dev and prod never run at the same time.
dev: infra migrate
	$(UV) python main.py

front:
	cd frontend && npm run dev

prod: build
	$(COMPOSE_DEV) down
	$(COMPOSE_PROD) up -d --wait

prod-down:
	$(COMPOSE_PROD) down

prod-logs:
	$(COMPOSE_PROD) logs -f backend

lint:
	cd backend && uv run ruff check . && uv run ruff format --check . && uv run pyright
	cd frontend && npm run lint && npm run typecheck

fmt:
	cd backend && uv run ruff format . && uv run ruff check --fix .
	cd frontend && npm run fmt

typecheck:
	cd backend && uv run pyright
	cd frontend && npm run typecheck

test:
	$(COMPOSE_DEV) up -d --wait postgres-test
	cd backend && uv run pytest $(args)
	cd frontend && npm test

gen:
	cd backend && uv run python -m api.openapi_export > ../frontend/openapi.json
	cd frontend && npm run gen

migration:
	@test -n "$(m)" || (echo 'usage: make migration m="message"' && exit 1)
	$(UV) alembic revision --autogenerate -m "$(m)"

migrate:
	$(UV) alembic upgrade head

build: build-backend build-web

build-backend:
	docker build -f docker/backend.Dockerfile -t club110-backend:latest .

build-web:
	docker build -f docker/web.Dockerfile -t club110-web:latest .

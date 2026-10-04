SHELL := /bin/bash
.DEFAULT_GOAL := help
.PHONY: help infra infra-down dev prod prod-down prod-logs lint fmt typecheck test migration migrate build

COMPOSE_DEV := docker compose -f docker-compose.yml -f docker-compose.dev.yml
COMPOSE_PROD := docker compose -p club110-prod
UV := cd backend && DB_HOST=localhost REDIS_HOST=localhost uv run --env-file ../.env

help:
	@echo "dev         infra in docker + backend on the host (debugger, fast restart)"
	@echo "prod        full stack in docker exactly as on the server (own containers and volumes)"
	@echo "prod-down   stop the prod stack"
	@echo "prod-logs   follow backend logs of the prod stack"
	@echo "infra       start postgres, redis, postgres-test in docker"
	@echo "infra-down  stop dev infra"
	@echo "lint        ruff check + ruff format --check + pyright"
	@echo "fmt         ruff format + ruff check --fix"
	@echo "test        run pytest against postgres-test"
	@echo "migration   autogenerate alembic revision: make migration m=\"add lessons\""
	@echo "migrate     alembic upgrade head on the dev database"
	@echo "build       build backend docker image club110-backend:latest"

infra:
	$(COMPOSE_PROD) down
	$(COMPOSE_DEV) up -d --wait postgres redis postgres-test

infra-down:
	$(COMPOSE_DEV) down

# One bot token allows a single getUpdates consumer, so dev and prod never run at the same time.
dev: infra migrate
	$(UV) python main.py

prod: build
	$(COMPOSE_DEV) down
	$(COMPOSE_PROD) up -d --wait

prod-down:
	$(COMPOSE_PROD) down

prod-logs:
	$(COMPOSE_PROD) logs -f backend

lint:
	cd backend && uv run ruff check . && uv run ruff format --check . && uv run pyright

fmt:
	cd backend && uv run ruff format . && uv run ruff check --fix .

typecheck:
	cd backend && uv run pyright

test:
	$(COMPOSE_DEV) up -d --wait postgres-test
	cd backend && uv run pytest $(args)

migration:
	@test -n "$(m)" || (echo 'usage: make migration m="message"' && exit 1)
	$(UV) alembic revision --autogenerate -m "$(m)"

migrate:
	$(UV) alembic upgrade head

build:
	docker build -f docker/backend.Dockerfile -t club110-backend:latest .

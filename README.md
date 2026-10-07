# 110 Club Bot

Telegram bot and admin panel for the "110" clubs of the "100балльный репетитор" online school.

The bot links a student's Telegram account to their VK profile, syncs club membership per study block from a Google Sheet,
lets members into the club chat and removes them when a block ends, and posts lesson and homework reminders
with materials to a dedicated forum topic. Lessons, homework and materials are managed in a React admin panel.

## Stack

- **Backend:** Python 3.13, aiogram 3, FastAPI, SQLAlchemy 2 (async), pydantic, dishka, alembic, APScheduler
- **Frontend:** React, TypeScript, Vite, Mantine, TanStack Query, API client generated from OpenAPI with orval
- **Infrastructure:** PostgreSQL, Redis, nginx, Docker Compose, GitHub Actions

## Development

Requirements: [uv](https://docs.astral.sh/uv/), Node.js 24+, Docker, make.

```bash
cp .env.example .env   # fill in the secrets
make dev               # postgres + redis in docker, backend on the host
make front             # admin panel dev server on http://localhost:5173
make prod              # the whole stack in docker, as on the server (admin panel on http://localhost:8080)
make lint
make test
```

Run `make help` for the full list of commands.

## Deployment

The stack exposes a single plain-HTTP port, `127.0.0.1:${WEB_PORT}` (8080 by default): the `web` container serves the
admin panel and proxies `/api/*` to the backend. TLS and the domain are handled by the reverse proxy on the host,
for example nginx:

```nginx
server {
    server_name admin.example.com;
    # listen 443 ssl; ssl_certificate ...;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        # Overwrite, never append: login attempts are rate-limited per client IP taken from this header.
        proxy_set_header X-Forwarded-For $remote_addr;
    }
}
```

## License

[MIT](LICENSE)

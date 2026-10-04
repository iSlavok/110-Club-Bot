# 110 Club Bot

Telegram bot and admin panel for the "110" clubs of the "100балльный репетитор" online school.

The bot links a student's Telegram account to their VK profile, syncs club membership per study block from a Google Sheet,
lets members into the club chat and removes them when a block ends, and posts lesson and homework reminders
with materials to a dedicated forum topic. Lessons, homework and materials are managed in a React admin panel.

## Stack

- **Backend:** Python 3.13, aiogram 3, FastAPI, SQLAlchemy 2 (async), pydantic, dishka, alembic, APScheduler
- **Infrastructure:** PostgreSQL, Redis, Docker Compose, GitHub Actions
- **Frontend:** React (planned)

## Development

Requirements: [uv](https://docs.astral.sh/uv/), Docker, make.

```bash
cp .env.example .env   # fill in the secrets
make dev               # postgres + redis in docker, backend on the host
make prod              # the whole stack in docker, as on the server
make lint
make test
```

Run `make help` for the full list of commands.

## License

[MIT](LICENSE)

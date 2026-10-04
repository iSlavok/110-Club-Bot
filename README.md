# 110 Club Bot

Telegram bot and admin panel for the "110" clubs of the "100балльный репетитор" online school.

The bot links a student's Telegram account to their VK profile, syncs club membership per study block from a Google Sheet,
lets members into the club chat and removes them when a block ends, and posts lesson and homework reminders
with materials to a dedicated forum topic. Lessons, homework and materials are managed in a React admin panel.

## Stack

- **Backend:** Python 3.13, aiogram 3, FastAPI, SQLAlchemy 2 (async), pydantic, dishka, alembic, APScheduler
- **Infrastructure:** PostgreSQL, Redis, Docker Compose, GitHub Actions
- **Frontend:** React (planned)

## License

[MIT](LICENSE)

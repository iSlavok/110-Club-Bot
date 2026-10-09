# 110 Club Bot

Telegram-бот + веб-админка для клубов «110» онлайн-школы «100балльный репетитор».
Бот: привязка Telegram к VK, синк состава клуба по блокам с Google Sheets, впуск в чат и исключение, напоминания об уроках и дедлайнах ДЗ в топик чата. Админка: создание уроков, ДЗ, материалов, управление участниками.

`docs/` — локальные заметки владельца (в `.gitignore`): `decisions.md` — решения + причины, `backlog.md` — задачи, `architecture.md` — текущее устройство. Перед фичей читай `docs/decisions.md` и раздел фичи в `docs/backlog.md`, если папка есть. Правила кода — только здесь, в CLAUDE.md.

## Структура репозитория

| Путь | Что |
|---|---|
| `backend/` | Python: ядро `app/` + транспорты `api/` (FastAPI), `bot/` (aiogram), `worker/` (периодические задачи), один процесс. Свой `pyproject.toml` и `uv.lock`. |
| `backend/migrations/` | Alembic. |
| `backend/tests/` | pytest. |
| `frontend/` | React-админка. Правила в `frontend/CLAUDE.md`. |
| `docker/` | Dockerfile'ы (`backend`, `web` = сборка админки + nginx), `nginx.conf`. |
| `docker-compose.yml` | Эталонная топология для одного VPS. |
| `Makefile` | Оркестратор, делегирует в backend и frontend. |

## Команды

```bash
make infra       # postgres, redis, postgres-test в docker (порты только на 127.0.0.1)
make dev         # infra в docker + migrate + backend на хосте (отладчик, быстрый рестарт)
make front       # админка: Vite :5173, /api проксируется на backend :8000 (рядом с make dev)
make prod        # весь стек в docker как на сервере (отдельный compose-проект club110-prod), админка на http://localhost:8080
make prod-down   # остановить prod-стек; make prod-logs — логи backend
make lint        # backend: ruff + pyright; frontend: eslint + prettier + tsc
make fmt         # форматирование backend и frontend
make test        # pytest против postgres-test (:5433) + vitest; аргументы pytest: make test args="-k user --cov"
make gen         # OpenAPI из backend → frontend/openapi.json → orval-клиент
make migration m="add lessons"   # alembic autogenerate против dev-базы
make migrate     # alembic upgrade head
make build       # docker-образы club110-backend:latest и club110-web:latest
```

Env — `.env` в корне (шаблон `.env.example`). Там только секреты и имена; хосты по умолчанию (`postgres`, `redis`) заданы в `Settings` под docker-сеть. Запуск на хосте: `Makefile` подставляет `DB_HOST=localhost REDIS_HOST=localhost`, запускает `uv run --env-file ../.env` из `backend/`. Run configuration в PyCharm — то же: `.env` + эти две переменные. Python-окружение — `backend/.venv`.

Меняешь/добавляешь команду — обнови раздел.

## Сквозные правила

- **Зависимости направлены в одну сторону.** Backend: `models ← repositories/queries ← services ← api / bot / worker`. Frontend: `shared ← entities ← features ← pages ← app`. Нарушение = ошибка, не стиль.
- **Контракт API генерируется.** Pydantic-схемы ответов → `openapi.json` → orval → TS-типы и хуки. Сгенерированный код руками не правим. Изменил схему → `make gen`, коммить оба конца. CI проверяет пустой `git diff` после генерации.
- **Тесты обязательны при изменении логики.** Добавил/удалил/изменил поведение (сервис, репозиторий, хендлер, роут, компонент, хук) → в том же изменении пиши/правь/удаляй тесты. Без тестов не готово. Багфикс начинается с красного теста, воспроизводящего баг.
- **Комментарии и коммиты на английском**, документация и CLAUDE.md на русском.
- **Весь IO асинхронный**, event loop не блокируем. Синхронная библиотека — через `asyncio.to_thread`.

## Git и репозиторий

Репозиторий публичный.

**Ветки:**
- `main` — только выпущенные версии. Каждый мерж в `main` → тег `vX.Y.Z` + GitHub Release.
- `release/X.Y.Z` — разработка версии. От `main`, в `main` одним PR через merge commit.
- `feat/*`, `fix/*`, `chore/*` — один PR на фичу/этап, всегда в текущий `release/*`, мерж rebase'ом.
- `hotfix/*` — от `main`, мерж в `main` с patch-тегом и обратно в текущий `release/*`.

**Коммиты:**
- Коммит, пуш, PR — только по команде. Сначала покажи изменения.
- Conventional Commits на английском со scope: `feat(sync): ...`, `fix(bot): ...`. Тема в повелительном наклонении.
- Фичи мержатся rebase'ом → каждый коммит в истории: один коммит = одно логическое изменение, проходит lint и тесты. Никаких «fix typo», «review fixes»: правки по ревью — `git commit --fixup <sha>`, перед мержем `git rebase -i --autosquash`, затем force-push ветки фичи.
- pre-commit проверяет рабочее дерево, не будущий коммит. Правка затрагивает несколько исходных коммитов → промежуточный fixup может не пройти pyright. Такие fixup'ы — с `SKIP=pyright,ruff-check,ruff-format`: проверки секретов остаются. После autosquash каждый коммит — через `git rebase --exec` (ruff, pyright, pytest), вся ветка — через `pre-commit run --from-ref release/X.Y.Z --to-ref HEAD`.
- Перед коммитом: `git status` + полный staged-дифф. Файлы добавляй явно, без слепого `git add -A`.

**Секреты и персональные данные:**
- В git никогда: `.env`, ключи, токены, JSON-ключи сервисных аккаунтов, реальные VK id, имена, любые данные учеников (в т.ч. в тестах, фикстурах, миграциях, примерах). В тестах — только выдуманные данные.
- В `.env.example` значения секретов всегда пустые.
- gitleaks проверяет коммиты в pre-commit и CI. Сработал → не обходи, убери секрет. Секрет попал в историю → считай скомпрометированным, перевыпусти.

## Backend

Python 3.13, uv, aiogram 3, FastAPI, SQLAlchemy 2 (async, asyncpg), pydantic v2, pydantic-settings, dishka, alembic, APScheduler (+ apscheduler-dishka), loguru.

### Слои

```
backend/
  app/            ядро без транспорта: не импортирует aiogram-хендлеры, FastAPI-роуты и worker
    config/       pydantic-settings
    database/     Base, BaseRepository, engine/sessionmaker factory
    models/       ORM, одна таблица — один файл
    repositories/ один репозиторий на модель
    queries/      read-агрегации по нескольким моделям (+ rows/)
    services/     use-cases, бизнес-логика; не коммитят — транзакция на весь запрос
    schemas/      pydantic: DTO моделей, команды (XCreate / XUpdate) и прочее, что сервисы принимают и отдают
    clients/      внешние API: Google Sheets, VK, хранилище файлов
    exceptions/   доменные исключения
    texts/        все тексты для пользователей: ответы бота, напоминания, алерты
    enums/  types/  utils/
    ioc/          dishka-провайдеры
  api/            FastAPI: роуты, схемы ответов (`schemas/`), auth-зависимости, exception handlers
  bot/            aiogram: роутеры, хендлеры, клавиатуры, callback data, middlewares
  worker/         APScheduler: регистрация и функции периодических задач
  main.py         composition root: запуск api + bot + worker
```

Backend — один процесс: `backend/main.py` (composition root) читает настройки, собирает один dishka-контейнер, запускает в `asyncio.TaskGroup` api (uvicorn), bot (polling), worker (APScheduler). Падение любой задачи валит процесс, рестарт — docker.

- `api/`, `bot/`, `worker/` друг друга не импортируют, общаются только через сервисы и БД. Общего in-memory состояния между транспортами нет → можно разнести по процессам без переписывания.
- Нет глобального состояния уровня модуля: никаких `settings = Settings()`, engine или `Bot` при импорте. Всё создаётся в composition root, раздаётся через dishka.

### Модели

- `Base` уже содержит `id`, `created_at`, `updated_at`, `__tablename__`. Не объявляй повторно. `MetaData` с naming convention.
- Enum-колонки только через `str_enum(X)` из `app/database`: в БД строка (`.value`), без нативного PG enum.
- Все datetime — `DateTime(timezone=True)`, в UTC.
- `Base` включает `eager_defaults`: серверные значения (`created_at`, `updated_at`, `server_default`) приходят через `RETURNING` сразу после flush. Без этого обращение к ним после `commit()` — ленивая загрузка, в async падает `MissingGreenlet`.
- Отношения — `Mapped[...]`, импорты типов под `TYPE_CHECKING`.

### Repositories и queries

- SQLAlchemy `select` / `insert` / `update` / `delete` — **только** в `app/repositories/` и `app/queries/`. Сервисы, роуты, хендлеры, задачи запросов не пишут — нужен запрос → метод в репозиторий.
- Одна модель — один репозиторий: `class LessonRepository(BaseRepository[Lesson])`, сессия в конструктор.
- Репозиторий принимает примитивы (keyword-only), не pydantic-схемы: схемы — контракт сервисов с верхними слоями, не с БД.
- Запрос собирается в переменную `statement`, выполняется отдельной строкой. Всегда в скобках, каждый вызов цепочки — на своей строке, даже если вызов один. В `.where()` больше одного условия — каждое на своей строке с запятой в конце. Подзапрос для `exists()` и скалярные подзапросы — отдельные переменные, итоговый `select(sub.exists())` / `select(a, b)` из готовых частей — одной строкой:
  ```python
  statement = (
      select(Block)
      .where(
          Block.club_id == club_id,
          Block.sheet_column_title == sheet_column_title,
      )
  )
  ```
- `app/repositories/` и `app/queries/` исключены из `ruff format` (он склеивает цепочки обратно), формат там держится вручную; `ruff check` работает как обычно.
- Репозиторий возвращает ORM-объекты, только сервисам. Нужные выше связи грузятся жадно внутри метода: «многие к одному» (`session.admin_user`, `admin.role`) — `joinedload`, один запрос с JOIN; «один ко многим» — `selectinload`, без размножения строк. Ленивые связи наверх не отдаются.
- Список страницами — один метод репозитория → `PageResult[Model]` (`items`, `total`). Условия собираются один раз в `conditions`, из них оба запроса: `select(func.count()).select_from(Model).where(*conditions)` и запрос страницы с сортировкой, `limit` / `offset`. Отдельных `count_*` под список не пишем: фильтры разойдутся.
- Нечёткий поиск — `pg_trgm`: служебная generated-колонка с нормализованным текстом + GIN `gin_trgm_ops`, запрос нормализуется так же (`normalize_search_query`), порог `word_similarity` — явно в запросе, не через `set_limit`.
- Join/агрегация по нескольким моделям — класс `XQueries(session)`, возвращает dataclass `XRow` из `app/queries/rows/`. Дальше сервиса `XRow` не уходит.

### Services

- Зависимости (сессия, репозитории, queries, клиенты, `Bot`) — через конструктор. Создаёт контейнер, сервис сам ничего не создаёт.
- **Транзакция — одна на действие, коммитит DI.** Один request scope (HTTP-запрос, апдейт бота, запуск задачи) = одна транзакция: `DatabaseProvider` коммитит при выходе из scope без исключения и откатывает при исключении. `commit()` не пишет никто: ни сервисы, ни роуты, ни хендлеры, ни задачи — поэтому сервисы свободно вызывают друг друга в одном действии. Роуты, хендлеры и задачи `AsyncSession` не получают.
- Сервис делает `await self._x_repository.flush()`, когда результат записи нужен дальше в том же действии: `id` и серверные значения для DTO, удаление, которое сразу проверяют, запись, которую нужно гарантировать до внешнего эффекта (код входа до отправки в бот).
- Уникальность и существование — SELECT'ом в сервисе до записи (`get_by_title` → `ClubTitleTakenError`). Ограничение в БД остаётся страховкой: при гонке двух запросов второй получит 500, для админки это приемлемо.
- Задача над многими элементами открывает свой scope на элемент (`async with container() as scope:`), чтобы ошибка одного не откатила остальные.
- Наверх — pydantic-модели из `app/schemas/` или примитивы, не ORM. ORM → DTO через classmethod `from_orm_obj` с явным перечислением полей. `model_validate(orm, from_attributes=True)` не используем: неявно обходит связи, прячет, какие поля уходят наверх.
- `XDTO` — зеркало модели `X`: все колонки, включая `id`, `created_at`, `updated_at`. Кроме служебных, которые ведёт сама БД или которые нельзя выпускать (поисковые `search_text`, хэши токенов). Отбор полей — дело схем ответа API. `XWith<Связь>DTO(XDTO)` — плюс связь, загруженная жадно в репозитории (`AdminUserWithRoleDTO.role`). Суффикс `With` — только для связей, не для подмножества колонок. Классы, которые не отражают таблицу (`AdminPrincipal`, `SessionGrant`, команды `XCreate` / `XUpdate`), суффикс `DTO` не носят.
- Ошибки — доменные исключения из `app/exceptions/`. Никаких `HTTPException` и ответов aiogram в сервисах.
- Сетевые ошибки клиентов (`app/clients/`) выше сервиса не уходят: сервис ловит, бросает доменную ошибку.

### DI (dishka)

- `DatabaseProvider`: engine и sessionmaker в `Scope.APP`, сессия в `Scope.REQUEST`. Одна сессия на HTTP-запрос, апдейт бота или запуск задачи; провайдер коммитит её на выходе из scope или откатывает, если scope закрылся исключением (dishka передаёт его в генератор).
- `RepositoriesProvider`, `QueriesProvider`, `ServicesProvider` — через `provide_all`. Новый класс = одна строка в провайдере. «Сервис не резолвится» почти всегда = не добавили туда.
- `Settings` в контейнер через `from_context`, `SettingsProvider` раздаёт части (`DatabaseSettings`, `BotSettings`, ...). Зависи от нужной части, не от всего `Settings`. `Bot`, Redis, клиенты — в `Scope.APP`. Ресурсы с закрытием — `yield`-провайдеры.
- FastAPI: `attach_container(app, container)` и `APIRouter(route_class=UnitOfWorkRoute)` из `api/core/routing.py`, параметры `FromDishka[...]`. `setup_dishka` для FastAPI не используем: его middleware открывает scope вокруг всего приложения — доменная ошибка превращается в ответ раньше, чем доходит до `DatabaseProvider` (коммит вместо отката), а коммит случается после отправки ответа. `UnitOfWorkRoute` открывает scope вокруг самого роута (проверяет `tests/api/test_unit_of_work.py`). aiogram: `setup_dishka(container, router=dp, auto_inject=True)`. APScheduler: `apscheduler-dishka` — `setup_dishka(container=..., scheduler=..., auto_inject=True)` в `create_scheduler`, задачи — обычный `scheduler.add_job(job, trigger)`; на каждый запуск свой request scope, исключение задачи доходит до `DatabaseProvider` (откат).

### API (FastAPI)

- Роут: вызывает сервис, возвращает результат. Доменные исключения не ловит, в `HTTPException` не превращает — это делает общий `app_error_handler`.
- `HTTPException` не используем совсем: guard'ы auth тоже бросают доменные `NotAuthenticatedError` / `PermissionDeniedError` — формат ошибки один.
- Доступ — только `require(...)` прямо в роуте, без алиасов и констант в начале файла: `dependencies=[require(Permission.X)]`; нужен сам админ — параметр `actor: Annotated[AdminPrincipal, require(Permission.X)]`; `require()` без права — любой вошедший. Право — enum `Permission` + строка в `PERMISSION_CATALOG` (подпись и группа для админки). Выдавать права ролям и роли админам — только через `ensure_within_own_permissions`.
- Владельцы (`AUTH_OWNER_IDS`) не в БД: все права, админка их не правит. Сессия — непрозрачный токен в httpOnly cookie, в БД только sha256.
- DTO и прочие модели из `app/schemas/` наружу не уходят. Роут всегда мапит результат сервиса в схему ответа из `api/schemas/` через `from_dto` (или `from_<имя>`). В API попадают только явно перечисленные поля, новое поле DTO не утечёт во фронт само.
- Тело запроса один в один с командой сервиса (create, update, PATCH) → роут принимает внутреннюю схему из `app/schemas/`, передаёт в сервис как есть. HTTP-специфичное тело — отдельная схема в `api/schemas/`.
- Схемы в OpenAPI описывают поля через `Field(description=...)`: из них генерируется фронт.
- Целые во входных данных ограничены типом колонки: поля схем — `BigInt`, `PositiveBigInt`, `PositiveInt32` из `app/types`, id в путях — `IdPath` из `api/core/params.py`. Значение, которое не влезет в колонку, должно падать валидацией (422), а не запросом в БД (500). Строки, которые потом идут в криптографию или парсинг, — с `pattern`.
- Списки — общая пагинация, свою в каждом роуте не изобретай. Параметры — модель `PageParams` (`page` с 1, `per_page`) или наследник с фильтрами, через `Annotated[..., Query()]`: FastAPI разворачивает модель, только если она единственный query-параметр. Сервис отдаёт `Paginated[T]` (`items`, `total`), роут — `Page.from_paginated(...)` → `items`, `page`, `per_page`, `total_items`, `total_pages`.
- PATCH — `XUpdate(PatchSchema)` с полями `Maybe[T]` (не передано ≠ `null`), сервис применяет `patch.field.apply(obj.field)`, пустой патч → `EmptyUpdateError`. Ограничения — на внутреннем типе через `type`-алиас с `Annotated`; `AwareDatetime` внутри `Maybe` — только как `Annotated[datetime, AwareDatetime]`.
- Роутеры подключаются в одном месте с префиксом `/api/v1/...`.
- Пробы `/livez` и `/readyz` вне `/api/v1`, не в OpenAPI. `/readyz` проверяет все внешние зависимости с таймаутом, отвечает `200` или `503` со списком `checks`.

### Bot (aiogram)

- Хендлеры тонкие: разобрать апдейт, вызвать сервис, ответить. Бизнес-логики нет.
- Тексты для пользователя — в `app/texts/`, не строками в хендлерах и клавиатурах: их собирают и хендлеры, и сервисы / worker, а ядро `bot/` не импортирует.
- Callback data — только классы `CallbackData`, без сырых строк.
- Порядок outer middlewares важен: ошибки → контейнер → пользователь. Ошибки снаружи контейнера: перехваченная доменная ошибка должна выйти из request scope исключением, иначе частичные изменения закоммитятся (проверяет `tests/bot/test_dispatcher.py`).
- Отправка в Telegram — через общий rate limiter. `TelegramForbiddenError` (бот заблокирован) — ожидаемо, не ошибка.

### Worker

- Задача — плоская функция с параметрами `FromDishka[...]`: вызывает сервис, сама ничего не собирает. Каждый запуск — новый request scope.
- Задача над многими элементами ловит исключение на каждый элемент: один сломанный не останавливает остальные.
- Задачи идемпотентны: повторный запуск после падения не шлёт дублей. Состояние «отправлено / не отправлено» — в БД, не в памяти планировщика.

### Исключения

- Базовые теги в `app/exceptions/base.py`: `NotFoundError`, `InvalidInputError`, `ConflictError`, `AuthenticationError`, `AuthorizationError`, `ExternalServiceError` и т. д. Каждое доменное исключение наследует **ровно один** тег.
- `code` выводится из имени класса (`LessonNotFoundError` → `LESSON_NOT_FOUND`). HTTP-статус на исключении не хранится: тег → статус только в API exception handler, разрешается по MRO.
- Один формат ошибки на всё API: `{"code": "LESSON_NOT_FOUND", "message": "..."}`. Ошибки валидации запроса — `VALIDATION_FAILED`, необработанные — `INTERNAL_ERROR` без деталей.
- Бот ловит доменные исключения в error middleware, отвечает текстом из `app/texts/`.

### Настройки

- Инфраструктура и секреты — `app/config/settings.py`: корневой `Settings` (pydantic-settings), вложенная `BaseModel` на каждую область. `DB_HOST` → `settings.db.host`: разделитель `_`, одно разбиение. Секреты — `SecretStr`. Добавил поле → обнови `.env.example` с комментарием.
- Настройки создаются в composition root, передаются через DI, не импортируются глобально.

### Время

- В БД и схемах API — UTC. Бизнес-время (расписание, «сегодня», текст напоминаний) — `Europe/Moscow`. «Сегодня» по UTC не считай. Текущее время — из `Clock` в DI, чтобы подменять в тестах.

### Миграции

- Схемные миграции — только autogenerate (`make migration`), затем ревью и ручная правка (server_default, nullable, backfill). Автокомментарии `# ### commands auto generated` удаляй.
- `create_all` в приложении и тестах не используется: схема всегда через alembic.
- Data-миграции руками, идемпотентны: `insert(...).on_conflict_do_nothing(...)`, без f-string SQL.
- Миграции выполняет отдельный one-shot сервис `migrate`, не `CMD` приложения.

### Тесты

- Общие фикстуры: `db_session`, `container` / `request_container` (тестовый dishka), `clock` (`FrozenClock`) — в `tests/conftest.py`; `api_client` (httpx) и `login_as(admin)` (сессия в cookie клиента) — в `tests/api/conftest.py`. Владелец в тестах — `OWNER_TG_ID` из `tests/providers.py`. Тестовые провайдеры — `tests/providers.py`, фейки — `tests/fakes.py`.
- Структура: `tests/unit/` (без БД и IO), `tests/integration/` (Postgres), `tests/api/` (httpx `ASGITransport`), `tests/bot/`, `tests/worker/`. Файл теста повторяет путь модуля.
- Настоящий Postgres, схема через `alembic upgrade head`. Изоляция: транзакция на тест с откатом. Тестовая сессия не коммитит: сервисы и проверки работают в одной сессии, поэтому забытый коммит тесты бы не поймали — его делает только `DatabaseProvider` (у него свой тест).
- Зависимости — из **тестового dishka-контейнера**: прод-провайдеры + тестовая сессия, фейковые клиенты (Google Sheets, VK, хранилище), `AsyncMock(spec=Bot)`, фиксированный `Clock`. Граф руками не собирается.
- Данные — только фабрики из `tests/factories.py`, голые конструкторы моделей в тестах запрещены. Новая модель → новая фабрика.
- API-тесты проверяют статус и тело, включая `code`.
- Bot-тесты проверяют эффект в БД и ответ пользователю.
- Coverage-порог — храповик: только растёт.

### Стиль

- PEP 695 generics (`class BaseRepository[ModelType: Base]`), аннотации типов везде.
- `await` не прячем внутри выражения (`X.from_dto(await ...)`, `bool(await ...)`, `[... for x in await ...]`, `total=await ...` в аргументах): результат — в переменную, отдельной строкой преобразование. `return await repo.get(...)` без обёртки — можно.
- Имя файла компонента слоя — с суффиксом слоя, сущность в единственном числе: `club_repository.py`, `club_service.py`, `dashboard_queries.py`, `dashboard_rows.py`, `club_schemas.py` (и в `app/schemas/`, и в `api/schemas/`), роуты — во множественном: `clubs_routes.py`. Класс-помощник без суффикса слоя — файл по имени класса (`admin_access_resolver.py`). Без суффикса: `models/` (`club.py`), `enums/`, `exceptions/`, `texts/` (`auth.py`), бот (`handlers/start.py`) и технические модули (`database/`, `config/`, `ioc/`, `utils/`, `api/core/`). Тест — `test_<имя модуля>.py`.
- `__init__.py` — только импорты и `__all__`. Фабрики, роутеры, прочая логика — в отдельных модулях (`router.py`, `container.py`).
- ruff (line length 120, двойные кавычки, trailing commas), `ruff format`. pyright без ошибок. Версии ruff и pyright в pre-commit, CI и `uv.lock` совпадают.
- Без `print`: только loguru, плейсхолдеры `{}` вместо f-строк.
- `noqa` и `type: ignore` — только с конкретным кодом и только когда правильно исправить нельзя.

## Комментарии

По умолчанию комментария нет. Имена заменяют объяснения, функции — блоки с заголовками. Комментарий — только если отвечает на вопрос, на который код ответить не может.

**Пиши комментарий только для:**
- почему так, а не очевидным способом: назови отвергнутый вариант и причину;
- внешнего ограничения (библиотека, протокол, лимит Telegram API, порядок инициализации);
- бизнес-правила или инварианта, которого нет в коде;
- предупреждения редактору («меняй вместе с X»).

**Никогда не пиши:**
- пересказ имени или сигнатуры;
- докстринг ради докстринга;
- «где это используется»;
- баннеры над группами полей;
- пошаговый пересказ алгоритма;
- историю правок («раньше было», «добавлено для»);
- закомментированный код;
- TODO без ссылки на задачу.

**Форма:** английский, ≤2 строк (жёсткий предел 4). Не влезает → место в CLAUDE.md или документации. Над блоком, утверждением о системе, без «мы», «теперь», «здесь».

**Тест удалением:** мысленно удали комментарий. Никто не спросит то, на что он отвечал → удаляй. Спросит → сократи до ответа. При правке кода удаляй устаревшие комментарии рядом, саму правку не комментируй.

Исключение: `Field(description=...)` в схемах API — контракт, не комментарий. Попадает в OpenAPI и во фронт.

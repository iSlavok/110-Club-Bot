# Frontend — админка

React 19 + TypeScript (strict) + Vite, Mantine 9, TanStack Query 5, React Router 8, dayjs. Тесты — Vitest + Testing Library + MSW. npm, Node 24+.

TypeScript закреплён на 6.x: typescript-eslint пока не поддерживает 7.x. Обновлять вместе.

## Команды (из `frontend/`)

```bash
npm run dev        # Vite :5173, /api проксируется на backend :8000 (make dev в соседнем терминале)
npm run lint       # eslint + prettier --check
npm run typecheck  # tsc --noEmit
npm test           # vitest run
npm run build
npm run gen        # orval из openapi.json; из корня — make gen (сначала выгружает схему из backend)
```

## Структура (Feature-Sliced)

```
src/
  app/        провайдеры, QueryClient, роутер, guard'ы, layout с меню
  pages/      страница = файл; собирает features/entities, своей логики почти нет
  features/   действия пользователя: формы, модалки, подтверждения (вход, клуб, блок, админ, роль)
  entities/   доменные кирпичи без действий: сессия и права, статус блока, группировка прав
  shared/     api (сгенерированный клиент + http-мутатор), lib (даты, ошибки, уведомления, пагинация), ui, config
  test/       setup, MSW-сервер, фикстуры, render-хелперы
```

- Слой импортирует только слои ниже: `shared ← entities ← features ← pages ← app`. Проверяет eslint (`no-restricted-imports`), нарушение — ошибка.
- Слайсы одного слоя друг друга не импортируют. Нужно общее — опусти ниже.
- Слайс отдаёт наружу только то, что в его `index.ts`.
- Импорты между слоями — через алиас `@/`.

## API

- Клиент генерирует orval из `openapi.json` в `src/shared/api/generated/`. Руками не правим. Изменилась схема бэка → `make gen`, коммить `openapi.json` и `generated/` вместе с бэком. CI сверяет.
- Импорт — только из `@/shared/api` (хуки, типы, `ApiError`).
- Запросы идут на тот же origin (`/api/v1/...`), сессия — httpOnly cookie. Токенов в JS нет.
- Ошибка API → `ApiError { status, code, message, fields }`. Текст пользователю — `errorMessage(error)` по `code` (`shared/lib/errors.ts`). Новый код ошибки на бэке → строка там же. Ошибки полей 422 → `form.setErrors(fieldErrors(error))`.
- После любой успешной мутации `QueryClient` инвалидирует все запросы, кроме `/auth/me`. Руками `invalidateQueries` в фичах не зови.
- 401 на любом запросе → перезапрос `/auth/me` → guard уводит на `/login`.

## Права

- Видимость кнопок — `<Can permission="...">`, проверка в коде — `usePermission` / `hasPermission`. Раздел целиком — `RequirePermission` в роутере.
- Выдать можно только свои права (`canGrant`): роли и админов сильнее себя UI не предлагает. Бэк проверяет то же самое, UI лишь не показывает заведомо запрещённое.

## Время

- API отдаёт и принимает UTC. Пользователю — Москва: `formatDateTime` / `formatDate`. Пикеры Mantine работают со строкой московского времени: `toPickerValue` / `fromPickerValue`.

## Формы и модалки

- `useForm` из `@mantine/form`, базовая валидация на клиенте, окончательная — на бэке.
- Модалка создания/редактирования рендерится, только пока открыта, с `key` по объекту: начальные значения формы берутся при монтировании.

## Тесты

- Обязательны при изменении логики компонента, хука, утилиты. Файл теста лежит рядом: `X.test.tsx`.
- Сеть — только через MSW (`server.use(...)` в тесте), неперехваченный запрос роняет тест.
- Рендер — `renderWithProviders(ui)` или `renderRoutes(routes)` из `@/test/render`. Сессия — `meHandler(makeAdmin(...permissions))`.
- Проверяй то, что видит пользователь (роли, подписи, текст), а не внутреннее состояние.

## Стиль

- Prettier (single quotes, 100 символов), typescript-eslint strict type-checked. `eslint-disable` и `as` — только когда правильно нельзя, с причиной.
- Тексты интерфейса на русском, прямо в компонентах.
- Комментарии — по правилам корневого `CLAUDE.md`.

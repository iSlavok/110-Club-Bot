import { http, HttpResponse } from 'msw';

import type { CurrentAdminResponse, Permission } from '@/shared/api';

export function makeAdmin(...permissions: Permission[]): CurrentAdminResponse {
  return { id: 1, tg_id: 1001, name: 'Тестовый админ', is_owner: false, permissions };
}

/** Serves `all` as `Page[T]` the way the API does, honouring `page` and `per_page` from the request. */
export function pageOf(all: unknown[], request: Request) {
  const params = new URL(request.url).searchParams;
  const page = Number(params.get('page') ?? 1);
  const perPage = Number(params.get('per_page') ?? 50);
  return HttpResponse.json({
    items: all.slice((page - 1) * perPage, page * perPage),
    page,
    per_page: perPage,
    total_items: all.length,
    total_pages: Math.ceil(all.length / perPage),
  });
}

export function meHandler(admin: CurrentAdminResponse | null) {
  return http.get('/api/v1/auth/me', () =>
    admin
      ? HttpResponse.json(admin)
      : HttpResponse.json(
          { code: 'NOT_AUTHENTICATED', message: 'Not authenticated' },
          { status: 401 },
        ),
  );
}

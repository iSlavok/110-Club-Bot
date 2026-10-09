import { http, HttpResponse } from 'msw';

import type { ClubResponse, CurrentAdminResponse, Permission } from '@/shared/api';

export function makeAdmin(...permissions: Permission[]): CurrentAdminResponse {
  return { id: 1, tg_id: 1001, name: 'Тестовый админ', is_owner: false, permissions };
}

export function makeClub(id: number, overrides: Partial<ClubResponse> = {}): ClubResponse {
  return {
    id,
    title: `Клуб ${id}`,
    chat_id: null,
    reminders_topic_id: null,
    spreadsheet_id: null,
    sheet_name: null,
    is_active: true,
    ...overrides,
  };
}

/** The club list and each club by id, as the API serves them. */
export function clubsHandlers(clubs: ClubResponse[]) {
  return [
    http.get('/api/v1/clubs', ({ request }) => pageOf(clubs, request)),
    http.get('/api/v1/clubs/:clubId', ({ params }) => {
      const club = clubs.find((item) => String(item.id) === params.clubId);
      return club
        ? HttpResponse.json(club)
        : HttpResponse.json({ code: 'CLUB_NOT_FOUND', message: 'not found' }, { status: 404 });
    }),
  ];
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

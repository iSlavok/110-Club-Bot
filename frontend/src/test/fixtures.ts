import { http, HttpResponse } from 'msw';

import type {
  ClubResponse,
  CurrentAdminResponse,
  LessonResponse,
  Permission,
  ReminderResponse,
} from '@/shared/api';

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

export function makeLesson(id: number, overrides: Partial<LessonResponse> = {}): LessonResponse {
  return {
    id,
    club_id: 1,
    kind: 'lesson',
    title: `Урок ${id}`,
    description: null,
    starts_at: '2026-10-03T16:00:00Z',
    call_url: null,
    is_cancelled: false,
    reminder_offsets: [1440, 60, 0],
    homework_deadline_at: null,
    homework_reminder_offsets: [2880, 1440, 180],
    ...overrides,
  };
}

export function makeReminder(
  id: number,
  overrides: Partial<ReminderResponse> = {},
): ReminderResponse {
  return {
    id,
    lesson: {
      id: 1,
      kind: 'lesson',
      title: 'Кислоты',
      starts_at: '2026-10-03T16:00:00Z',
      is_cancelled: false,
    },
    kind: 'lesson_upcoming',
    send_at: '2026-10-02T16:00:00Z',
    status: 'pending',
    attempts: 0,
    sent_at: null,
    error: null,
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

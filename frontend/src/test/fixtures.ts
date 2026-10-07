import { http, HttpResponse } from 'msw';

import type { CurrentAdminResponse, Permission } from '@/shared/api';

export function makeAdmin(...permissions: Permission[]): CurrentAdminResponse {
  return { id: 1, tg_id: 1001, name: 'Тестовый админ', is_owner: false, permissions };
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

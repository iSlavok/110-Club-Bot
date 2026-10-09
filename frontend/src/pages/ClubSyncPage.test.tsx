import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import type { Permission, SheetSyncResponse } from '@/shared/api';
import { clubsHandlers, makeAdmin, makeClub, meHandler, pageOf } from '@/test/fixtures';
import { renderRoutes } from '@/test/render';
import { server } from '@/test/server';

import { ClubSyncPage } from './ClubSyncPage';

const SHEET_CLUB = makeClub(7, { spreadsheet_id: 'sheet-1', sheet_name: 'Состав' });

function makeSync(id: number, overrides: Partial<SheetSyncResponse> = {}): SheetSyncResponse {
  return {
    id,
    club_id: 7,
    started_at: '2026-10-01T09:00:00Z',
    finished_at: '2026-10-01T09:00:02Z',
    status: 'ok',
    added: 0,
    removal_requested: 0,
    issues: [],
    error: null,
    ...overrides,
  };
}

function renderSync({
  club = SHEET_CLUB,
  history = [] as SheetSyncResponse[],
  permissions = [] as Permission[],
} = {}) {
  server.use(
    meHandler(makeAdmin('clubs.view', ...permissions)),
    ...clubsHandlers([club]),
    http.get('/api/v1/clubs/7/stats', () =>
      HttpResponse.json({ current_block: null, last_sync: history[0] ?? null }),
    ),
    http.get('/api/v1/clubs/7/syncs', ({ request }) => pageOf(history, request)),
  );
  return renderRoutes([{ path: '/clubs/:clubId/sync', element: <ClubSyncPage /> }], {
    route: '/clubs/7/sync',
  });
}

describe('ClubSyncPage', () => {
  it('shows the last sync with its problems and the history', async () => {
    const last = makeSync(2, {
      added: 3,
      removal_requested: 2,
      issues: [{ kind: 'invalid_value', column: 'Блок 5', row: 4, value: 'abc' }],
    });
    const failed = makeSync(1, { status: 'failed', error: 'Google Sheets API error 403' });
    renderSync({ history: [last, failed] });

    expect(await screen.findByText('Проблемы в таблице: 1')).toBeInTheDocument();
    expect(
      screen.getByText('Столбец «Блок 5», строка 4: «abc» — не VK id, пропущено'),
    ).toBeInTheDocument();
    expect(await screen.findByText('Google Sheets API error 403')).toBeInTheDocument();
    expect(screen.getAllByText('· на удаление: 2')).toHaveLength(2);
  });

  it('says when the club was never synced', async () => {
    renderSync();

    expect(await screen.findAllByText('Синков ещё не было')).toHaveLength(2);
  });

  it('runs a sync for admins with sync.run', async () => {
    let synced = false;
    server.use(
      http.post('/api/v1/clubs/7/sync', () => {
        synced = true;
        return HttpResponse.json(makeSync(3, { added: 5 }));
      }),
    );
    renderSync({ permissions: ['sync.run'] });

    await userEvent.click(await screen.findByRole('button', { name: 'Синхронизировать' }));

    expect(await screen.findByText('Синк выполнен: добавлено 5')).toBeInTheDocument();
    expect(synced).toBe(true);
  });

  it('hides the sync button without sync.run', async () => {
    renderSync();

    expect(await screen.findAllByText('Синков ещё не было')).toHaveLength(2);
    expect(screen.queryByRole('button', { name: 'Синхронизировать' })).not.toBeInTheDocument();
  });

  it('disables the sync for a club without a sheet', async () => {
    renderSync({ club: makeClub(7), permissions: ['sync.run'] });

    expect(
      await screen.findByText(
        'Синк идёт только у включённых клубов с указанными таблицей и листом.',
      ),
    ).toBeInTheDocument();
    expect(await screen.findByRole('button', { name: 'Синхронизировать' })).toBeDisabled();
  });
});

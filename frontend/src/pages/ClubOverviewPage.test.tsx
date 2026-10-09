import { screen } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import type { ClubStatsResponse } from '@/shared/api';
import { renderRoutes } from '@/test/render';
import { server } from '@/test/server';

import { ClubOverviewPage } from './ClubOverviewPage';

function renderOverview(stats: ClubStatsResponse) {
  server.use(http.get('/api/v1/clubs/7/stats', () => HttpResponse.json(stats)));
  return renderRoutes([{ path: '/clubs/:clubId', element: <ClubOverviewPage /> }], {
    route: '/clubs/7',
  });
}

describe('ClubOverviewPage', () => {
  it('shows the current block and its members', async () => {
    renderOverview({
      current_block: {
        block: {
          id: 3,
          club_id: 7,
          title: 'Блок 5',
          sheet_column_title: 'Блок 5',
          starts_at: '2026-09-01T00:00:00Z',
          ends_at: '2099-11-01T00:00:00Z',
        },
        members: 120,
        members_with_tg: 95,
      },
      last_sync: null,
    });

    expect(await screen.findByText('Блок 5')).toBeInTheDocument();
    expect(screen.getByText('120')).toBeInTheDocument();
    expect(screen.getByText('95')).toBeInTheDocument();
  });

  it('says when no block is running', async () => {
    renderOverview({ current_block: null, last_sync: null });

    expect(await screen.findByText('Сейчас блока нет')).toBeInTheDocument();
  });

  it('shows the last sheet sync and links to its page', async () => {
    renderOverview({
      current_block: null,
      last_sync: {
        id: 1,
        club_id: 7,
        started_at: '2026-10-01T09:00:00Z',
        finished_at: '2026-10-01T09:00:02Z',
        status: 'failed',
        added: 0,
        removal_requested: 0,
        issues: [],
        error: 'Google Sheets API error 403',
      },
    });

    expect(await screen.findByText('Ошибка')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Подробнее' })).toHaveAttribute(
      'href',
      '/clubs/7/sync',
    );
  });

  it('says when the club was never synced', async () => {
    renderOverview({ current_block: null, last_sync: null });

    expect(await screen.findByText('Синков ещё не было')).toBeInTheDocument();
  });
});

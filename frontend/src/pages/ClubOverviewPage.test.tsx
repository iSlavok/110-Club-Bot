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
    });

    expect(await screen.findByText('Блок 5')).toBeInTheDocument();
    expect(screen.getByText('120')).toBeInTheDocument();
    expect(screen.getByText('95')).toBeInTheDocument();
  });

  it('says when no block is running', async () => {
    renderOverview({ current_block: null });

    expect(await screen.findByText('Сейчас блока нет')).toBeInTheDocument();
  });
});

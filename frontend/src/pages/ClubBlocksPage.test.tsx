import { screen } from '@testing-library/react';
import { http } from 'msw';
import { describe, expect, it } from 'vitest';

import type { BlockListItemResponse, Permission } from '@/shared/api';
import { makeAdmin, meHandler, pageOf } from '@/test/fixtures';
import { renderRoutes } from '@/test/render';
import { server } from '@/test/server';

import { ClubBlocksPage } from './ClubBlocksPage';

const BLOCK: BlockListItemResponse = {
  id: 3,
  club_id: 7,
  title: '5',
  sheet_column_title: 'Блок 5',
  starts_at: '2026-09-01T00:00:00Z',
  ends_at: '2099-11-01T00:00:00Z',
  members_count: 2,
};

function renderBlocks(...permissions: Permission[]) {
  server.use(
    meHandler(makeAdmin('clubs.view', ...permissions)),
    http.get('/api/v1/clubs/7/blocks', ({ request }) => pageOf([BLOCK], request)),
  );
  renderRoutes([{ path: '/clubs/:clubId/blocks', element: <ClubBlocksPage /> }], {
    route: '/clubs/7/blocks',
  });
}

describe('ClubBlocksPage', () => {
  it('links the member count to the block page for admins with users.view', async () => {
    renderBlocks('users.view');

    expect(await screen.findByRole('link', { name: 'Участники блока 5' })).toHaveAttribute(
      'href',
      '/clubs/7/blocks/3',
    );
  });

  it('shows only the member count without users.view', async () => {
    renderBlocks();

    expect(await screen.findByText('Блок 5')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Участники блока 5' })).not.toBeInTheDocument();
  });
});

import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http } from 'msw';
import { describe, expect, it } from 'vitest';

import type { BlockListItemResponse, BlockMemberResponse, Permission } from '@/shared/api';
import { makeAdmin, meHandler, pageOf } from '@/test/fixtures';
import { revealListEnds } from '@/test/intersection';
import { renderRoutes } from '@/test/render';
import { server } from '@/test/server';

import { ClubBlocksPage } from './ClubBlocksPage';

const BLOCK: BlockListItemResponse = {
  id: 3,
  club_id: 7,
  title: 'Блок 5',
  sheet_column_title: 'Блок 5',
  starts_at: '2026-09-01T00:00:00Z',
  ends_at: '2099-11-01T00:00:00Z',
  members_count: 2,
};

const MEMBERS: BlockMemberResponse[] = [
  { vk_id: 501, user: { id: 1, full_name: 'Анна Белова', tg_username: 'anna' } },
  { vk_id: 502, user: null },
];

function renderBlocks(...permissions: Permission[]) {
  server.use(
    meHandler(makeAdmin('clubs.view', ...permissions)),
    http.get('/api/v1/clubs/7/blocks', ({ request }) => pageOf([BLOCK], request)),
    http.get('/api/v1/blocks/3/members', ({ request }) => pageOf(MEMBERS, request)),
  );
  return renderRoutes([{ path: '/clubs/:clubId/blocks', element: <ClubBlocksPage /> }], {
    route: '/clubs/7/blocks',
  });
}

describe('ClubBlocksPage', () => {
  it('opens the members of a block for admins with users.view', async () => {
    renderBlocks('users.view');

    await userEvent.click(await screen.findByRole('button', { name: 'Участники блока Блок 5' }));
    revealListEnds();

    const modal = within(await screen.findByRole('dialog'));
    expect(await modal.findByText('Анна Белова')).toBeInTheDocument();
    expect(modal.getByText('@anna')).toBeInTheDocument();
    expect(modal.getByRole('link', { name: 'id502' })).toHaveAttribute(
      'href',
      'https://vk.com/id502',
    );
    expect(modal.getByText('не подключил бота')).toBeInTheDocument();
  });

  it('shows only the member count without users.view', async () => {
    renderBlocks();

    expect(await screen.findAllByText('Блок 5')).toHaveLength(2);
    expect(screen.getByText('2')).toBeInTheDocument();
    expect(
      screen.queryByRole('button', { name: 'Участники блока Блок 5' }),
    ).not.toBeInTheDocument();
  });
});

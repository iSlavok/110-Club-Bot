import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import type { BlockMemberResponse, BlockResponse } from '@/shared/api';
import { makeAdmin, meHandler, pageOf } from '@/test/fixtures';
import { revealListEnds } from '@/test/intersection';
import { renderRoutes } from '@/test/render';
import { server } from '@/test/server';

import { ClubBlockPage } from './ClubBlockPage';

const BLOCK: BlockResponse = {
  id: 3,
  club_id: 7,
  title: 'Блок 5',
  sheet_column_title: 'Блок 5',
  starts_at: '2026-09-01T00:00:00Z',
  ends_at: '2099-11-01T00:00:00Z',
};

const MEMBERS: BlockMemberResponse[] = [
  {
    vk_id: 501,
    user: {
      id: 1,
      full_name: 'Анна Белова',
      tg_username: 'anna',
      chat_status: 'joined',
      chat_joined_at: '2026-09-02T10:00:00Z',
    },
  },
  { vk_id: 502, user: null },
];

function renderBlock() {
  const requests: URLSearchParams[] = [];
  server.use(
    meHandler(makeAdmin('clubs.view', 'users.view')),
    http.get('/api/v1/blocks/3', () => HttpResponse.json(BLOCK)),
    http.get('/api/v1/blocks/3/members/funnel', () =>
      HttpResponse.json({ total: 2, with_bot: 1, in_chat: 1 }),
    ),
    http.get('/api/v1/blocks/3/members', ({ request }) => {
      requests.push(new URL(request.url).searchParams);
      return pageOf(MEMBERS, request);
    }),
  );
  renderRoutes([{ path: '/clubs/:clubId/blocks/:blockId', element: <ClubBlockPage /> }], {
    route: '/clubs/7/blocks/3',
  });
  return requests;
}

describe('ClubBlockPage', () => {
  it('lists the members with their bot user and chat state', async () => {
    renderBlock();
    revealListEnds();

    expect(await screen.findByText('Анна Белова')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: '@anna' })).toHaveAttribute(
      'href',
      'https://t.me/anna',
    );
    expect(screen.getByRole('link', { name: 'id502' })).toHaveAttribute(
      'href',
      'https://vk.com/id502',
    );
    expect(screen.getByText('не подключил бота')).toBeInTheDocument();
    expect(screen.getByText('в чате')).toBeInTheDocument();
  });

  it('filters by the funnel step, with its count, and searches', async () => {
    const requests = renderBlock();

    await screen.findByText('Анна Белова');
    await userEvent.click(await screen.findByText('Без бота · 1'));
    await waitFor(() => {
      expect(requests.at(-1)?.get('state')).toBe('no_bot');
    });
    await userEvent.type(screen.getByRole('textbox', { name: 'Поиск' }), 'анна');
    await waitFor(() => {
      expect(requests.at(-1)?.get('q')).toBe('анна');
    });
    expect(requests.at(-1)?.get('state')).toBe('no_bot');
    expect(screen.getByRole('link', { name: 'Скачать .xlsx' })).toHaveAttribute(
      'href',
      '/api/v1/blocks/3/members/export?state=no_bot&q=%D0%B0%D0%BD%D0%BD%D0%B0',
    );
  });

  it('sorts by the pressed column, bot users first by default', async () => {
    const requests = renderBlock();

    await screen.findByText('Анна Белова');
    expect(requests.at(-1)?.get('sort')).toBe('bot');
    await userEvent.click(screen.getByRole('button', { name: /Чат/ }));
    await waitFor(() => {
      expect([requests.at(-1)?.get('sort'), requests.at(-1)?.get('order')]).toEqual([
        'chat',
        'asc',
      ]);
    });
  });
});

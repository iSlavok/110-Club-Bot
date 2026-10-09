import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import type { UserResponse } from '@/shared/api';
import { renderWithProviders } from '@/test/render';
import { server } from '@/test/server';

import { UsersPage } from './UsersPage';

const ANNA: UserResponse = {
  id: 1,
  tg_id: 111,
  tg_username: 'anna',
  full_name: 'Анна Белова',
  vk_id: 42,
  vk_linked_at: '2026-09-02T09:00:00Z',
  created_at: '2026-09-01T09:00:00Z',
};

describe('UsersPage', () => {
  it('searches users on the server', async () => {
    server.use(
      http.get('/api/v1/users', ({ request }) => {
        const q = new URL(request.url).searchParams.get('q');
        const items = q === 'анна' ? [ANNA] : [];
        return HttpResponse.json({
          items,
          page: 1,
          per_page: 50,
          total_items: items.length,
          total_pages: 1,
        });
      }),
    );
    renderWithProviders(<UsersPage />);

    expect(await screen.findByText('Никого не нашли')).toBeInTheDocument();
    await userEvent.type(screen.getByLabelText('Поиск'), 'анна');

    expect(await screen.findByText('Анна Белова')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'id42' })).toHaveAttribute(
      'href',
      'https://vk.com/id42',
    );
    expect(screen.getByText('02.09.2026 12:00')).toBeInTheDocument();
  });
});

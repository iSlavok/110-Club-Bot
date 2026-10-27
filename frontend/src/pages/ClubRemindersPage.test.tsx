import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http } from 'msw';
import { describe, expect, it } from 'vitest';

import type { Permission } from '@/shared/api';
import { makeAdmin, meHandler, pageOf } from '@/test/fixtures';
import { renderRoutes } from '@/test/render';
import { server } from '@/test/server';

import { ClubRemindersPage } from './ClubRemindersPage';

function renderPage(...permissions: Permission[]) {
  server.use(
    meHandler(makeAdmin('lessons.view', ...permissions)),
    http.get('/api/v1/clubs/1/reminders', ({ request }) => pageOf([], request)),
    http.get('/api/v1/clubs/1/lessons', ({ request }) => pageOf([], request)),
  );
  renderRoutes([{ path: '/clubs/:clubId/reminders', element: <ClubRemindersPage /> }], {
    route: '/clubs/1/reminders',
  });
}

describe('ClubRemindersPage', () => {
  it('opens the message form with messages.send', async () => {
    renderPage('messages.send');

    await userEvent.click(await screen.findByRole('button', { name: 'Сообщение в чат' }));

    expect(await screen.findByRole('dialog', { name: 'Сообщение в чат' })).toBeInTheDocument();
  });

  it('hides the message button without messages.send', async () => {
    renderPage('lessons.edit');

    expect(await screen.findByText('Напоминаний нет')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Сообщение в чат' })).not.toBeInTheDocument();
  });
});

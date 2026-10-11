import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http } from 'msw';
import { describe, expect, it } from 'vitest';

import type { Permission } from '@/shared/api';
import { makeAdmin, makeLesson, meHandler, pageOf } from '@/test/fixtures';
import { renderRoutes } from '@/test/render';
import { server } from '@/test/server';

import { ClubLessonsPage } from './ClubLessonsPage';

function renderPage(...permissions: Permission[]) {
  const requests: URLSearchParams[] = [];
  server.use(
    meHandler(makeAdmin('lessons.view', ...permissions)),
    http.get('/api/v1/clubs/1/lessons', ({ request }) => {
      requests.push(new URL(request.url).searchParams);
      return pageOf(
        [
          makeLesson(5, { title: 'Кислоты', homework_deadline_at: '2026-10-06T20:59:00Z' }),
          makeLesson(6, { title: 'Оксиды', kind: 'curator_call', is_cancelled: true }),
        ],
        request,
      );
    }),
  );
  renderRoutes([{ path: '/clubs/:clubId/lessons', element: <ClubLessonsPage /> }], {
    route: '/clubs/1/lessons',
  });
  return requests;
}

describe('ClubLessonsPage', () => {
  it('lists upcoming lessons linked to their cards', async () => {
    const requests = renderPage();

    expect(await screen.findByRole('link', { name: 'Кислоты' })).toHaveAttribute(
      'href',
      '/clubs/1/lessons/5',
    );
    expect(screen.getByText('06.10.2026 23:59')).toBeInTheDocument();
    expect(screen.getByText('Созвон с куратором')).toBeInTheDocument();
    expect(screen.getByText('Отменён')).toBeInTheDocument();
    expect(requests[0]?.get('view')).toBe('upcoming');
    expect(requests[0]?.has('include_cancelled')).toBe(false);
    expect(screen.queryByRole('button', { name: 'Новый урок' })).not.toBeInTheDocument();
  });

  it('switches the view and shows cancelled lessons on request', async () => {
    const requests = renderPage('lessons.edit');

    await userEvent.click(await screen.findByText('Прошедшие'));
    await waitFor(() => {
      expect(requests.at(-1)?.get('view')).toBe('past');
    });
    await userEvent.click(screen.getByLabelText('Отменённые'));
    await waitFor(() => {
      expect(requests.at(-1)?.get('include_cancelled')).toBe('true');
    });
    expect(screen.getByRole('button', { name: 'Новый урок' })).toBeInTheDocument();
  });
});

import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import type { Permission, ReminderResponse } from '@/shared/api';
import { makeAdmin, makeLesson, makeReminder, meHandler, pageOf } from '@/test/fixtures';
import { renderWithProviders } from '@/test/render';
import { server } from '@/test/server';

import { ReminderFeed } from './ReminderFeed';

function serve(reminders: ReminderResponse[], ...permissions: Permission[]) {
  const requests: URLSearchParams[] = [];
  server.use(
    meHandler(makeAdmin('lessons.view', ...permissions)),
    http.get('/api/v1/clubs/1/reminders', ({ request }) => {
      requests.push(new URL(request.url).searchParams);
      return pageOf(reminders, request);
    }),
    http.get('/api/v1/clubs/1/lessons', ({ request }) =>
      pageOf([makeLesson(1, { title: 'Кислоты' }), makeLesson(2, { title: 'Оксиды' })], request),
    ),
  );
  return requests;
}

describe('ReminderFeed', () => {
  it('shows pending reminders first and switches views as query params', async () => {
    const requests = serve([
      makeReminder(1, { status: 'failed', error: 'Bad Request: chat not found' }),
    ]);
    renderWithProviders(<ReminderFeed clubId={1} />);

    expect(await screen.findByText('Bad Request: chat not found')).toBeInTheDocument();
    expect(screen.getByText('Напоминание об уроке')).toBeInTheDocument();
    expect(requests.at(-1)?.get('view')).toBe('pending');

    await userEvent.click(screen.getByLabelText('Отменённые'));
    await waitFor(() => {
      expect(requests.at(-1)?.get('include_cancelled')).toBe('true');
    });

    await userEvent.click(screen.getByText('Отправленные'));
    await waitFor(() => {
      expect(requests.at(-1)?.get('view')).toBe('sent');
    });
    expect(requests.at(-1)?.has('include_cancelled')).toBe(false);
    expect(screen.getByLabelText('Отменённые')).toBeDisabled();
  });

  it('filters by a lesson of the club', async () => {
    const requests = serve([makeReminder(1)]);
    renderWithProviders(<ReminderFeed clubId={1} />);

    await userEvent.click(await screen.findByRole('combobox', { name: 'Урок' }));
    // Mantine's dropdown transition hides options from role queries in jsdom; text finds them.
    await userEvent.click(await screen.findByText(/Оксиды/));

    await waitFor(() => {
      expect(requests.at(-1)?.get('lesson_id')).toBe('2');
    });
  });

  it('inside a lesson card asks only for that lesson and hides the lesson column', async () => {
    const requests = serve([makeReminder(1)]);
    renderWithProviders(<ReminderFeed clubId={1} lessonId={5} />);

    expect(await screen.findByText('Напоминание об уроке')).toBeInTheDocument();
    expect(requests.at(-1)?.get('lesson_id')).toBe('5');
    expect(screen.queryByRole('columnheader', { name: 'Урок' })).not.toBeInTheDocument();
    expect(screen.queryByRole('combobox', { name: 'Урок' })).not.toBeInTheDocument();
  });

  it('previews the message text', async () => {
    serve([makeReminder(7)]);
    server.use(
      http.get('/api/v1/reminders/7/preview', () =>
        HttpResponse.json({ html: '<b>Урок «Кислоты»</b>\nЗавтра в 19:00 (МСК)' }),
      ),
    );
    renderWithProviders(<ReminderFeed clubId={1} />);

    await userEvent.click(await screen.findByRole('button', { name: 'Текст' }));

    const preview = await screen.findByTestId('reminder-preview');
    expect(within(preview).getByText('Урок «Кислоты»').tagName).toBe('B');
    expect(preview).toHaveTextContent('Завтра в 19:00 (МСК)');
  });

  it('cancels a pending reminder after confirmation', async () => {
    let cancelled = false;
    serve([makeReminder(3), makeReminder(4, { status: 'sent' })], 'lessons.edit');
    server.use(
      http.post('/api/v1/reminders/3/cancel', () => {
        cancelled = true;
        return HttpResponse.json(makeReminder(3, { status: 'cancelled' }));
      }),
    );
    renderWithProviders(<ReminderFeed clubId={1} />);

    const buttons = await screen.findAllByRole('button', { name: 'Отменить' });
    expect(buttons).toHaveLength(1);
    await userEvent.click(buttons[0] ?? document.body);
    await userEvent.click(await screen.findByRole('button', { name: 'Отменить напоминание' }));

    await waitFor(() => {
      expect(cancelled).toBe(true);
    });
  });

  it('hides cancelling without lessons.edit', async () => {
    serve([makeReminder(3)]);
    renderWithProviders(<ReminderFeed clubId={1} />);

    expect(await screen.findByRole('button', { name: 'Текст' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Отменить' })).not.toBeInTheDocument();
  });
});

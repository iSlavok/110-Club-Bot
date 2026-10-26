import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import type { LessonResponse, Permission } from '@/shared/api';
import { makeAdmin, makeLesson, meHandler, pageOf } from '@/test/fixtures';
import { renderRoutes } from '@/test/render';
import { server } from '@/test/server';

import { ClubLessonPage } from './ClubLessonPage';

function renderCard(lesson: LessonResponse, ...permissions: Permission[]) {
  const reminderRequests: URLSearchParams[] = [];
  server.use(
    meHandler(makeAdmin('lessons.view', ...permissions)),
    http.get(`/api/v1/lessons/${lesson.id}`, () => HttpResponse.json(lesson)),
    http.get('/api/v1/clubs/1/reminders', ({ request }) => {
      reminderRequests.push(new URL(request.url).searchParams);
      return pageOf([], request);
    }),
  );
  renderRoutes([{ path: '/clubs/:clubId/lessons/:lessonId', element: <ClubLessonPage /> }], {
    route: `/clubs/1/lessons/${lesson.id}`,
  });
  return reminderRequests;
}

describe('ClubLessonPage', () => {
  it('shows the lesson, its homework and its reminders', async () => {
    const requests = renderCard(
      makeLesson(5, {
        kind: 'curator_call',
        title: 'Кислоты',
        call_url: 'https://meet.example.com/abc',
        description: 'Повторить оксиды',
        homework_deadline_at: '2026-10-06T20:59:00Z',
        homework_reminder_offsets: [1440, 0],
      }),
    );

    expect(await screen.findByRole('heading', { name: 'Кислоты' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'https://meet.example.com/abc' })).toBeInTheDocument();
    expect(screen.getByText('Повторить оксиды')).toBeInTheDocument();
    expect(screen.getByText('за 1 день, за 1 час, в момент начала')).toBeInTheDocument();
    expect(screen.getByText('за 1 день, в момент дедлайна')).toBeInTheDocument();
    expect(screen.getByText('06.10.2026 23:59')).toBeInTheDocument();
    await waitFor(() => {
      expect(requests.at(-1)?.get('lesson_id')).toBe('5');
    });
    expect(screen.queryByRole('button', { name: 'Отменить урок' })).not.toBeInTheDocument();
  });

  it('has no call link field for a lesson', async () => {
    renderCard(makeLesson(6, { title: 'Кислоты' }));

    expect(await screen.findByRole('heading', { name: 'Кислоты' })).toBeInTheDocument();
    expect(screen.queryByText('Ссылка на созвон')).not.toBeInTheDocument();
  });

  it('cancels the lesson and asks whether to tell the chat', async () => {
    let body: unknown;
    const lesson = makeLesson(7, { title: 'Кислоты' });
    renderCard(lesson, 'lessons.edit');
    server.use(
      http.post('/api/v1/lessons/7/cancel', async ({ request }) => {
        body = await request.json();
        return HttpResponse.json({ ...lesson, is_cancelled: true });
      }),
    );

    await userEvent.click(await screen.findByRole('button', { name: 'Отменить урок' }));
    const confirm = await screen.findByRole('dialog', { name: 'Отменить урок?' });
    await userEvent.click(within(confirm).getByRole('button', { name: 'Отменить урок' }));
    expect(await screen.findByText('Сообщить в чат об отмене урока?')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Не сообщать' }));

    await waitFor(() => {
      expect(body).toEqual({ notify_chat: false });
    });
  });

  it('hides editing for a cancelled lesson', async () => {
    renderCard(makeLesson(8, { is_cancelled: true }), 'lessons.edit');

    expect(await screen.findByText('Отменён')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Изменить' })).not.toBeInTheDocument();
  });

  it('sends a homework reminder now after showing its text', async () => {
    const lesson = makeLesson(7, {
      title: 'Кислоты',
      homework_deadline_at: '2099-10-06T20:59:00Z',
    });
    const previews: unknown[] = [];
    const reminds: unknown[] = [];
    renderCard(lesson, 'lessons.edit');
    server.use(
      http.post('/api/v1/reminders/preview', async ({ request }) => {
        previews.push(await request.json());
        return HttpResponse.json({ html: '<b>ДЗ к уроку «Кислоты»</b>' });
      }),
      http.post('/api/v1/lessons/7/remind', async ({ request }) => {
        reminds.push(await request.json());
        return HttpResponse.json({}, { status: 201 });
      }),
    );

    await userEvent.click(await screen.findByRole('button', { name: 'Напомнить сейчас' }));
    await userEvent.click(await screen.findByText('О дедлайне ДЗ'));

    expect(await screen.findByText('ДЗ к уроку «Кислоты»')).toBeInTheDocument();
    expect(previews.at(-1)).toMatchObject({
      kind: 'homework_deadline',
      lesson: { title: 'Кислоты', homework_deadline_at: '2099-10-06T20:59:00Z' },
    });
    await userEvent.click(screen.getByRole('button', { name: 'Отправить' }));

    await waitFor(() => {
      expect(reminds).toEqual([{ target: 'homework' }]);
    });
  });

  it('offers no homework reminder for a lesson without homework', async () => {
    renderCard(makeLesson(8), 'lessons.edit');
    server.use(http.post('/api/v1/reminders/preview', () => HttpResponse.json({ html: 'Урок' })));

    await userEvent.click(await screen.findByRole('button', { name: 'Напомнить сейчас' }));

    expect(await screen.findByTestId('reminder-preview')).toBeInTheDocument();
    expect(screen.queryByText('О дедлайне ДЗ')).not.toBeInTheDocument();
  });
});

import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import dayjs from 'dayjs';
import { http, HttpResponse } from 'msw';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { LessonResponse } from '@/shared/api';
import { makeLesson, makeSettings, settingsHandler } from '@/test/fixtures';
import { renderWithProviders } from '@/test/render';
import { server } from '@/test/server';

import { LessonFormModal } from './LessonFormModal';

const HOUR_MS = 3_600_000;

// Accessible name of a day in the open month of a picker.
const dayLabel = (day: number) => dayjs().date(day).locale('ru').format('D MMMM YYYY');

interface Patch {
  body: Record<string, unknown>;
  notify: string | null;
}

function servePatch(lesson: LessonResponse): Patch[] {
  const patches: Patch[] = [];
  server.use(
    http.patch(`/api/v1/lessons/${lesson.id}`, async ({ request }) => {
      patches.push({
        body: (await request.json()) as Record<string, unknown>,
        notify: new URL(request.url).searchParams.get('notify_chat'),
      });
      return HttpResponse.json(lesson);
    }),
  );
  return patches;
}

describe('LessonFormModal', () => {
  beforeEach(() => {
    server.use(settingsHandler());
  });

  it('prefills a new lesson with the default offsets from the bot settings', async () => {
    server.use(
      settingsHandler(
        makeSettings({ default_lesson_offsets: [1440, 0], default_homework_offsets: [180] }),
      ),
    );
    renderWithProviders(<LessonFormModal clubId={1} onClose={vi.fn()} />);

    // Options render hidden in jsdom: a selected offset shows twice, as its pill and its option.
    expect(await screen.findAllByText('за 1 день')).toHaveLength(2);
    expect(screen.getAllByText('в момент начала')).toHaveLength(2);
    expect(screen.getAllByText('за 1 час')).toHaveLength(1);
    await userEvent.click(screen.getByRole('button', { name: 'Сохранить' }));
    expect(await screen.findByText('Укажите тему')).toBeInTheDocument();
    expect(screen.getByText('Укажите начало')).toBeInTheDocument();
  });

  it('sets the default time when a day is picked for the start and the deadline', async () => {
    server.use(settingsHandler(makeSettings({ default_lesson_time: '15:30:00' })));
    renderWithProviders(<LessonFormModal clubId={1} onClose={vi.fn()} />);

    await userEvent.click(await screen.findByRole('button', { name: /Начало/ }));
    await userEvent.click(await screen.findByRole('button', { name: dayLabel(10) }));
    await userEvent.click(screen.getByRole('switch', { name: 'Есть ДЗ' }));
    await userEvent.click(screen.getByRole('button', { name: /Дедлайн ДЗ/ }));
    await userEvent.click(await screen.findByRole('button', { name: dayLabel(12) }));

    expect(screen.getByRole('button', { name: /Начало/ })).toHaveTextContent(/15:30$/);
    expect(screen.getByRole('button', { name: /Дедлайн ДЗ/ })).toHaveTextContent(/23:59$/);
  });

  it('previews a reminder of the unsaved lesson from its offset', async () => {
    const lesson = makeLesson(9, { title: 'Кислоты', starts_at: '2026-10-03T16:00:00Z' });
    const previews: unknown[] = [];
    server.use(
      http.post('/api/v1/reminders/preview', async ({ request }) => {
        previews.push(await request.json());
        return HttpResponse.json({ html: '<b>Урок «Основания»</b>' });
      }),
    );
    renderWithProviders(<LessonFormModal clubId={1} lesson={lesson} onClose={vi.fn()} />);

    const title = await screen.findByLabelText(/Тема/);
    await userEvent.clear(title);
    await userEvent.type(title, 'Основания');
    await userEvent.click(
      screen.getByRole('button', { name: 'Напоминания об уроке: текст «за 1 час»' }),
    );

    expect(await screen.findByText('Урок «Основания»')).toBeInTheDocument();
    expect(previews).toEqual([
      {
        kind: 'lesson_upcoming',
        send_at: '2026-10-03T15:00:00.000Z',
        lesson: {
          kind: 'lesson',
          title: 'Основания',
          starts_at: '2026-10-03T16:00:00.000Z',
          call_url: null,
          description: null,
          homework_deadline_at: null,
        },
      },
    ]);
  });

  it('previews the «now» reminder without a send time', async () => {
    const previews: { send_at: unknown }[] = [];
    server.use(
      http.post('/api/v1/reminders/preview', async ({ request }) => {
        previews.push((await request.json()) as { send_at: unknown });
        return HttpResponse.json({ html: 'Урок' });
      }),
    );
    renderWithProviders(<LessonFormModal clubId={1} lesson={makeLesson(10)} onClose={vi.fn()} />);

    await userEvent.click(
      await screen.findByRole('button', { name: 'Текст напоминания «сейчас»' }),
    );

    await waitFor(() => {
      expect(previews).toHaveLength(1);
    });
    expect(previews[0]?.send_at).toBeNull();
  });

  it('asks for the topic and start before previewing a new lesson', async () => {
    renderWithProviders(<LessonFormModal clubId={1} onClose={vi.fn()} />);

    await userEvent.click(
      await screen.findByRole('button', { name: 'Текст напоминания «сейчас»' }),
    );

    expect(await screen.findByText('Укажите тему')).toBeInTheDocument();
    expect(screen.getByText('Укажите начало')).toBeInTheDocument();
    expect(screen.queryByTestId('reminder-preview')).not.toBeInTheDocument();
  });

  it('saves a title change without asking about the chat', async () => {
    const lesson = makeLesson(3, { title: 'Кислоты' });
    const patches = servePatch(lesson);
    const onClose = vi.fn();
    renderWithProviders(<LessonFormModal clubId={1} lesson={lesson} onClose={onClose} />);

    const title = await screen.findByLabelText(/Тема/);
    await userEvent.clear(title);
    await userEvent.type(title, 'Основания');
    await userEvent.click(screen.getByRole('button', { name: 'Сохранить' }));

    await waitFor(() => {
      expect(onClose).toHaveBeenCalledOnce();
    });
    expect(screen.queryByText(/Сообщить в чат/)).not.toBeInTheDocument();
    expect(patches).toEqual([
      {
        notify: null,
        body: {
          kind: 'lesson',
          title: 'Основания',
          starts_at: '2026-10-03T16:00:00.000Z',
          call_url: null,
          description: null,
          reminder_offsets: [1440, 60, 0],
          homework_deadline_at: null,
          homework_reminder_offsets: [2880, 1440, 180],
        },
      },
    ]);
  });

  it.each([
    ['Сообщить', 'true'],
    ['Не сообщать', null],
  ])('removing homework asks about the chat: «%s»', async (answer, notify) => {
    const lesson = makeLesson(4, { homework_deadline_at: '2026-10-06T20:59:00Z' });
    const patches = servePatch(lesson);
    renderWithProviders(<LessonFormModal clubId={1} lesson={lesson} onClose={vi.fn()} />);

    await userEvent.click(await screen.findByRole('switch', { name: 'Есть ДЗ' }));
    await userEvent.click(screen.getByRole('button', { name: 'Сохранить' }));
    expect(await screen.findByText('Сообщить в чат об отмене ДЗ?')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: answer }));

    await waitFor(() => {
      expect(patches).toHaveLength(1);
    });
    expect(patches[0]?.notify).toBe(notify);
    expect(patches[0]?.body.homework_deadline_at).toBeNull();
  });

  it('warns when a homework reminder would come before the lesson', async () => {
    const lesson = makeLesson(5, {
      starts_at: '2026-10-03T16:00:00Z',
      homework_deadline_at: '2026-10-04T16:00:00Z',
      homework_reminder_offsets: [2880, 180],
    });
    renderWithProviders(<LessonFormModal clubId={1} lesson={lesson} onClose={vi.fn()} />);

    expect(await screen.findByText('Напоминание о ДЗ раньше урока')).toBeInTheDocument();
    expect(screen.getByText(/за 2 дня — уйдёт в чат ещё до начала урока/)).toBeInTheDocument();
  });

  it('offers the call link only for a curator call and drops it for a lesson', async () => {
    const call = makeLesson(7, { kind: 'curator_call', call_url: 'https://meet.example.com/abc' });
    const patches = servePatch(call);
    renderWithProviders(<LessonFormModal clubId={1} lesson={call} onClose={vi.fn()} />);

    expect(await screen.findByLabelText('Ссылка на созвон')).toHaveValue(
      'https://meet.example.com/abc',
    );
    await userEvent.click(screen.getByRole('radio', { name: 'Урок' }));
    expect(screen.queryByLabelText('Ссылка на созвон')).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Сохранить' }));

    await waitFor(() => {
      expect(patches).toHaveLength(1);
    });
    expect(patches[0]?.body).toMatchObject({ kind: 'lesson', call_url: null });
  });

  it('turns «remind now» into the minutes left before the start', async () => {
    // Whole minutes, as the picker keeps them: otherwise the start would look changed.
    const startsAt = new Date(
      Math.ceil((Date.now() + 2 * HOUR_MS) / 60_000) * 60_000,
    ).toISOString();
    const lesson = makeLesson(6, { starts_at: startsAt, reminder_offsets: [] });
    const patches = servePatch(lesson);
    renderWithProviders(<LessonFormModal clubId={1} lesson={lesson} onClose={vi.fn()} />);

    await userEvent.click(await screen.findByLabelText(/напомнить сейчас/));
    await userEvent.click(screen.getByRole('button', { name: 'Сохранить' }));

    await waitFor(() => {
      expect(patches).toHaveLength(1);
    });
    const [offset] = patches[0]?.body.reminder_offsets as number[];
    expect(offset).toBeGreaterThanOrEqual(119);
    expect(offset).toBeLessThanOrEqual(120);
  });
});

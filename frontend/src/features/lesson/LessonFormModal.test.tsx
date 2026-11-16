import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import dayjs from 'dayjs';
import { http, HttpResponse } from 'msw';
import { StrictMode } from 'react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { LessonResponse, PlatformCourseResponse, PlatformLessonResponse } from '@/shared/api';
import {
  clubsHandlers,
  makeClub,
  makeLesson,
  makeSettings,
  settingsHandler,
} from '@/test/fixtures';
import { renderWithProviders } from '@/test/render';
import { server } from '@/test/server';

import { LessonFormModal } from './LessonFormModal';

const HOUR_MS = 3_600_000;

// Accessible name of a day in the open month of a picker.
const dayLabel = (day: number) => dayjs().date(day).locale('ru').format('D MMMM YYYY');

// Looks the day up in the dropdown the picker opened: a role query over the whole modal is slow enough
// to time out on a loaded CI runner, and a label query would also find the other picker's hidden days.
async function pickDay(picker: RegExp, day: number) {
  const target = screen.getByRole('button', { name: picker });
  await userEvent.click(target);
  const dropdown = await waitFor(() => {
    const element = document.getElementById(target.getAttribute('aria-controls') ?? '');
    if (!element) {
      throw new Error('The picker dropdown is not open');
    }
    return element;
  });
  await userEvent.click(await within(dropdown).findByLabelText(dayLabel(day)));
}

const PLATFORM_COURSE: PlatformCourseResponse = {
  id: 7,
  title: 'Годовой курс',
  modules: [
    {
      id: 70,
      title: '1 блок',
      lessons: [
        {
          id: 701,
          title: 'Урок 1. Кислоты',
          is_published: true,
          starts_at: '2026-10-12T16:00:00Z',
          ends_at: null,
          linked: [
            { id: 3, title: 'Разбор', starts_at: '2026-10-12T16:00:00Z', is_cancelled: false },
          ],
        },
        {
          id: 702,
          title: 'Урок 2. Оксиды',
          is_published: false,
          starts_at: '2026-10-13T16:00:00Z',
          ends_at: null,
          linked: [],
        },
        {
          id: 703,
          title: 'Созвон с кураторами',
          is_published: true,
          starts_at: '2026-10-14T16:00:00Z',
          ends_at: null,
          linked: [],
        },
      ],
    },
  ],
  suggested_lesson_id: 702,
};

const PLATFORM_LESSON: PlatformLessonResponse = {
  id: 702,
  title: 'Урок 2. Оксиды',
  course_title: 'Годовой курс',
  module_title: '1 блок',
  is_published: false,
  starts_at: '2026-10-13T16:00:00Z',
  ends_at: '2026-10-13T18:00:00Z',
  publish_at: null,
  is_stop_lesson: false,
  call_url: null,
  homework: {
    deadline_at: '2026-10-16T20:59:00Z',
    summary: 'Выполни базовый уровень',
    levels: [
      {
        title: 'Базовый уровень',
        is_required: true,
        is_trial: true,
        time_limit_seconds: 10_800,
        task_count: 12,
      },
    ],
  },
  webinar: [{ title: 'Kinescope', url: 'https://kinescope.example.com/1' }],
  videos: [],
  materials: [{ title: 'Конспект.pdf', url: 'https://files.example.com/a.pdf' }],
  notes: [],
};

const ZOOM_URL = 'https://example.zoom.us/j/1234567';

const PLATFORM_CALL: PlatformLessonResponse = {
  ...PLATFORM_LESSON,
  id: 703,
  title: 'Созвон с кураторами',
  starts_at: '2026-10-14T16:00:00Z',
  ends_at: null,
  call_url: ZOOM_URL,
  homework: null,
  notes: [{ title: 'Привет!', text: `Ссылка на созвон по кнопке ниже\n${ZOOM_URL}` }],
};

function servePlatform() {
  server.use(
    ...clubsHandlers([makeClub(1, { platform_course_id: 7 })]),
    http.get('/api/v1/clubs/1/platform-course', () => HttpResponse.json(PLATFORM_COURSE)),
    http.get('/api/v1/platform/lessons/702', () => HttpResponse.json(PLATFORM_LESSON)),
    http.get('/api/v1/platform/lessons/703', () => HttpResponse.json(PLATFORM_CALL)),
  );
}

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
    server.use(settingsHandler(), ...clubsHandlers([makeClub(1)]));
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

    await screen.findByRole('button', { name: /Начало/ });
    await pickDay(/Начало/, 10);
    await userEvent.click(screen.getByRole('switch', { name: 'Есть ДЗ' }));
    await pickDay(/Дедлайн ДЗ/, 12);

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
          platform_lesson_id: null,
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
          platform_lesson_id: null,
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

  it('links a platform lesson and fills the empty start and deadline from it', async () => {
    servePlatform();
    let created: Record<string, unknown> | null = null;
    server.use(
      http.post('/api/v1/clubs/1/lessons', async ({ request }) => {
        created = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json(makeLesson(9), { status: 201 });
      }),
    );
    renderWithProviders(<LessonFormModal clubId={1} onClose={vi.fn()} />);

    await userEvent.click(await screen.findByRole('button', { name: /Урок на платформе/ }));
    const taken = await screen.findByRole('option', { hidden: true, name: /Урок 1\. Кислоты/ });
    expect(taken).toHaveTextContent('привязан: «Разбор» 12.10.2026');
    await userEvent.click(
      screen.getByRole('option', { hidden: true, name: /Урок 2\. Оксиды.*черновик/ }),
    );

    expect(
      await screen.findByText(
        'Базовый уровень · обязательное · заданий: 12 · пробник · на выполнение 3 ч',
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Начало/ })).toHaveTextContent('13.10.2026 19:00');
    expect(screen.getByRole('button', { name: /Дедлайн ДЗ/ })).toHaveTextContent(
      '16.10.2026 23:59',
    );
    expect(screen.queryByText(/у нас:/)).not.toBeInTheDocument();
    await userEvent.type(screen.getByRole('textbox', { name: /Тема/ }), 'Разбор оксидов');
    await userEvent.click(screen.getByRole('button', { name: 'Сохранить' }));

    await waitFor(() => {
      expect(created).toMatchObject({
        platform_lesson_id: 702,
        starts_at: '2026-10-13T16:00:00.000Z',
        homework_deadline_at: '2026-10-16T20:59:00.000Z',
      });
    });
  });

  it('fills the fields from the platform when the card remounts, as in development', async () => {
    servePlatform();
    renderWithProviders(
      <StrictMode>
        <LessonFormModal clubId={1} onClose={vi.fn()} />
      </StrictMode>,
    );

    await userEvent.click(await screen.findByRole('button', { name: /Урок на платформе/ }));
    await userEvent.click(
      await screen.findByRole('option', { hidden: true, name: /Урок 2\. Оксиды/ }),
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Начало/ })).toHaveTextContent('13.10.2026 19:00');
    });
  });

  it('keeps the start typed by the admin and offers the platform one', async () => {
    servePlatform();
    const lesson = makeLesson(6, { starts_at: '2026-10-13T15:00:00Z', platform_lesson_id: 702 });
    const patches = servePatch(lesson);
    renderWithProviders(<LessonFormModal clubId={1} lesson={lesson} onClose={vi.fn()} />);

    expect(await screen.findByText(/у нас: .* 18:00/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Урок на платформе/ })).toHaveTextContent(
      'Урок 2. Оксиды',
    );
    const [takeStart] = screen.getAllByRole('button', { name: 'Взять' });
    if (!takeStart) {
      throw new Error('No «Взять» button for the start');
    }
    await userEvent.click(takeStart);
    await userEvent.click(screen.getByRole('button', { name: 'Сохранить' }));
    await userEvent.click(await screen.findByRole('button', { name: /Не сообщать/ }));

    await waitFor(() => {
      expect(patches).toHaveLength(1);
    });
    expect(patches[0]?.body).toMatchObject({
      starts_at: '2026-10-13T16:00:00.000Z',
      platform_lesson_id: 702,
    });
  });

  it('unlinks the platform lesson', async () => {
    servePlatform();
    const lesson = makeLesson(6, { platform_lesson_id: 702 });
    const patches = servePatch(lesson);
    renderWithProviders(<LessonFormModal clubId={1} lesson={lesson} onClose={vi.fn()} />);

    await userEvent.click(await screen.findByRole('button', { name: /Урок на платформе/ }));
    await userEvent.click(
      await screen.findByRole('option', { hidden: true, name: '— не привязан' }),
    );
    await userEvent.click(screen.getByRole('button', { name: 'Сохранить' }));

    await waitFor(() => {
      expect(patches).toHaveLength(1);
    });
    expect(patches[0]?.body).toMatchObject({ platform_lesson_id: null });
  });

  it('makes a call of the lesson when the platform lesson has a Zoom link', async () => {
    servePlatform();
    let created: Record<string, unknown> | null = null;
    server.use(
      http.post('/api/v1/clubs/1/lessons', async ({ request }) => {
        created = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json(makeLesson(9), { status: 201 });
      }),
    );
    renderWithProviders(<LessonFormModal clubId={1} onClose={vi.fn()} />);

    await userEvent.click(await screen.findByRole('button', { name: /Урок на платформе/ }));
    await userEvent.click(
      await screen.findByRole('option', { hidden: true, name: /Созвон с кураторами/ }),
    );

    expect(await screen.findByRole('textbox', { name: 'Ссылка на созвон' })).toHaveValue(ZOOM_URL);
    expect(screen.getByRole('radio', { name: 'Созвон с куратором' })).toBeChecked();
    expect(screen.getByText(/Ссылка на созвон по кнопке ниже/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Открыть' })).toHaveAttribute(
      'href',
      'https://lk.100points.ru/teacher/course/7/lesson/703',
    );
    expect(screen.queryByText(/у нас:/)).not.toBeInTheDocument();
    await userEvent.type(screen.getByRole('textbox', { name: /Тема/ }), 'Созвон');
    await userEvent.click(screen.getByRole('button', { name: 'Сохранить' }));

    await waitFor(() => {
      expect(created).toMatchObject({
        kind: 'curator_call',
        call_url: ZOOM_URL,
        platform_lesson_id: 703,
        starts_at: '2026-10-14T16:00:00.000Z',
      });
    });
  });

  it('keeps a lesson linked to a call as typed and offers the Zoom link', async () => {
    servePlatform();
    const lesson = makeLesson(6, { starts_at: '2026-10-14T16:00:00Z', platform_lesson_id: 703 });
    const patches = servePatch(lesson);
    renderWithProviders(<LessonFormModal clubId={1} lesson={lesson} onClose={vi.fn()} />);

    expect(await screen.findByText('у нас: обычный урок')).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: 'Урок' })).toBeChecked();
    await userEvent.click(screen.getByRole('button', { name: 'Взять' }));
    await userEvent.click(screen.getByRole('button', { name: 'Сохранить' }));

    await waitFor(() => {
      expect(patches).toHaveLength(1);
    });
    expect(patches[0]?.body).toMatchObject({ kind: 'curator_call', call_url: ZOOM_URL });
  });

  it('has no platform field when the club has no platform course', async () => {
    renderWithProviders(<LessonFormModal clubId={1} onClose={vi.fn()} />);

    expect(await screen.findByRole('textbox', { name: /Тема/ })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Урок на платформе/ })).not.toBeInTheDocument();
  });
});

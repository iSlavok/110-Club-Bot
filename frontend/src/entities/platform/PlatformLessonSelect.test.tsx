import { fireEvent, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { expect, it, vi } from 'vitest';

import type { PlatformCourseResponse } from '@/shared/api';
import { renderWithProviders } from '@/test/render';
import { server } from '@/test/server';

import { PlatformLessonSelect } from './PlatformLessonSelect';

const lesson = (id: number, title: string) => ({
  id,
  title,
  is_published: true,
  starts_at: null,
  ends_at: null,
  linked: [],
});

const COURSE: PlatformCourseResponse = {
  id: 7,
  title: 'Годовой курс',
  modules: [
    { id: 1, title: '1 блок', lessons: [lesson(701, 'Урок 1. Кислоты')] },
    { id: 2, title: '2 блок', lessons: [lesson(702, 'Урок 2. Оксиды')] },
  ],
  suggested_lesson_id: null,
};

it('finds a lesson by a pasted student link', async () => {
  server.use(http.get('/api/v1/clubs/1/platform-course', () => HttpResponse.json(COURSE)));
  const onChange = vi.fn();
  renderWithProviders(<PlatformLessonSelect clubId={1} value={null} onChange={onChange} />);

  await userEvent.click(screen.getByRole('button', { name: /Урок на платформе/ }));
  await screen.findByRole('option', { hidden: true, name: /Кислоты/ });
  // The dropdown is hidden in jsdom: a click into it counts as a click outside and closes it.
  fireEvent.change(screen.getByPlaceholderText('Название, номер или ссылка на урок'), {
    target: { value: 'https://lk.100points.ru/student/lesson/702' },
  });

  expect(screen.queryByRole('option', { hidden: true, name: /Кислоты/ })).not.toBeInTheDocument();
  await userEvent.click(await screen.findByRole('option', { hidden: true, name: /Оксиды/ }));
  expect(onChange).toHaveBeenCalledWith(702);
});

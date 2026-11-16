import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { makeAdmin, makeClub, meHandler } from '@/test/fixtures';
import { renderRoutes } from '@/test/render';
import { server } from '@/test/server';

import { ClubSettingsPage } from './ClubSettingsPage';

describe('ClubSettingsPage', () => {
  it('turns on hiding join and leave messages', async () => {
    let body: unknown;
    const club = makeClub(7, { chat_id: -100500 });
    server.use(
      meHandler(makeAdmin('clubs.view', 'clubs.edit')),
      http.get('/api/v1/clubs/7', () => HttpResponse.json(club)),
      http.patch('/api/v1/clubs/7', async ({ request }) => {
        body = await request.json();
        return HttpResponse.json({ ...club, hide_service_messages: true });
      }),
    );
    renderRoutes([{ path: '/clubs/:clubId/settings', element: <ClubSettingsPage /> }], {
      route: '/clubs/7/settings',
    });

    expect(await screen.findByText('Показываются')).toBeInTheDocument();
    await userEvent.click(await screen.findByRole('button', { name: 'Изменить' }));
    const modal = within(await screen.findByRole('dialog'));
    await userEvent.click(
      modal.getByRole('switch', { name: /Скрывать сообщения о входе и выходе/ }),
    );
    await userEvent.click(modal.getByRole('button', { name: 'Сохранить' }));

    await waitFor(() => {
      expect(body).toMatchObject({ hide_service_messages: true });
    });
  });

  it('sets the status sheet', async () => {
    let body: unknown;
    const club = makeClub(7);
    server.use(
      meHandler(makeAdmin('clubs.view', 'clubs.edit')),
      http.get('/api/v1/clubs/7', () => HttpResponse.json(club)),
      http.patch('/api/v1/clubs/7', async ({ request }) => {
        body = await request.json();
        return HttpResponse.json({ ...club, status_sheet_name: 'Статус' });
      }),
    );
    renderRoutes([{ path: '/clubs/:clubId/settings', element: <ClubSettingsPage /> }], {
      route: '/clubs/7/settings',
    });

    await userEvent.click(await screen.findByRole('button', { name: 'Изменить' }));
    const modal = within(await screen.findByRole('dialog'));
    await userEvent.type(modal.getByRole('textbox', { name: /Лист статуса учеников/ }), 'Статус');
    await userEvent.click(modal.getByRole('button', { name: 'Сохранить' }));

    await waitFor(() => {
      expect(body).toMatchObject({ status_sheet_name: 'Статус' });
    });
  });

  it('takes the platform course from a pasted link', async () => {
    let body: unknown;
    const club = makeClub(7);
    server.use(
      meHandler(makeAdmin('clubs.view', 'clubs.edit')),
      http.get('/api/v1/clubs/7', () => HttpResponse.json(club)),
      http.patch('/api/v1/clubs/7', async ({ request }) => {
        body = await request.json();
        return HttpResponse.json({ ...club, platform_course_id: 4321 });
      }),
    );
    renderRoutes([{ path: '/clubs/:clubId/settings', element: <ClubSettingsPage /> }], {
      route: '/clubs/7/settings',
    });

    await userEvent.click(await screen.findByRole('button', { name: 'Изменить' }));
    const modal = within(await screen.findByRole('dialog'));
    const course = modal.getByRole('textbox', { name: /Курс на платформе/ });
    await userEvent.type(course, 'просто текст');
    await userEvent.click(modal.getByRole('button', { name: 'Сохранить' }));
    expect(await modal.findByText(/Вставьте ссылку на курс/)).toBeInTheDocument();
    await userEvent.clear(course);
    await userEvent.type(course, 'https://lk.100points.ru/teacher/courses/4321');
    await userEvent.click(modal.getByRole('button', { name: 'Сохранить' }));

    await waitFor(() => {
      expect(body).toMatchObject({ platform_course_id: 4321 });
    });
  });
});

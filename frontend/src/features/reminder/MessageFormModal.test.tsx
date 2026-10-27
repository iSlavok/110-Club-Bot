import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { describe, expect, it, vi } from 'vitest';

import type { ClubMessageCreate, ClubMessageUpdate, ReminderResponse } from '@/shared/api';
import { makeAdmin, makeMessage, meHandler } from '@/test/fixtures';
import { renderWithProviders } from '@/test/render';
import { server } from '@/test/server';

import { MessageFormModal } from './MessageFormModal';

function serveCreate(
  response: () => Response = () => HttpResponse.json(makeMessage(9), { status: 201 }),
) {
  const bodies: ClubMessageCreate[] = [];
  server.use(
    meHandler(makeAdmin('lessons.view', 'messages.send')),
    http.post('/api/v1/clubs/1/messages', async ({ request }) => {
      bodies.push((await request.json()) as ClubMessageCreate);
      return response();
    }),
  );
  return bodies;
}

function serveUpdate(message: ReminderResponse) {
  const bodies: ClubMessageUpdate[] = [];
  server.use(
    meHandler(makeAdmin('lessons.view', 'messages.send')),
    http.patch(`/api/v1/messages/${String(message.id)}`, async ({ request }) => {
      bodies.push((await request.json()) as ClubMessageUpdate);
      return HttpResponse.json(message);
    }),
  );
  return bodies;
}

async function typeIntoEditor(text: string) {
  await userEvent.click(await screen.findByRole('textbox'));
  await userEvent.keyboard(text);
}

describe('MessageFormModal', () => {
  it('sends the typed text right away and closes', async () => {
    const bodies = serveCreate();
    const onClose = vi.fn();
    renderWithProviders(<MessageFormModal clubId={1} onClose={onClose} />);

    await typeIntoEditor('Привет & пока');
    await userEvent.click(screen.getByRole('button', { name: 'Отправить' }));

    await waitFor(() => {
      expect(onClose).toHaveBeenCalled();
    });
    expect(bodies).toEqual([{ text: 'Привет &amp; пока', send_at: null }]);
  });

  it('formats with the toolbar and shows the result as it will look in the chat', async () => {
    const bodies = serveCreate();
    renderWithProviders(<MessageFormModal clubId={1} onClose={vi.fn()} />);

    await userEvent.click(await screen.findByRole('textbox'));
    await userEvent.click(screen.getByRole('button', { name: 'Жирный' }));
    await userEvent.keyboard('Запись');
    await userEvent.click(screen.getByRole('button', { name: 'Жирный' }));
    await userEvent.click(screen.getByRole('button', { name: 'Скрытый текст' }));
    await userEvent.keyboard(' уже тут');

    expect(screen.getByTestId('reminder-preview').innerHTML).toBe(
      '<b>Запись</b><span class="tg-spoiler"> уже тут</span>',
    );
    await userEvent.click(screen.getByRole('button', { name: 'Отправить' }));
    await waitFor(() => {
      expect(bodies[0]?.text).toBe('<b>Запись</b><span class="tg-spoiler"> уже тут</span>');
    });
  });

  it('asks for a text and, when scheduling, for a time', async () => {
    const bodies = serveCreate();
    renderWithProviders(<MessageFormModal clubId={1} onClose={vi.fn()} />);

    await userEvent.click(await screen.findByText('Запланировать'));
    await userEvent.click(screen.getByRole('button', { name: 'Запланировать' }));

    expect(await screen.findByText('Напишите сообщение')).toBeInTheDocument();
    expect(screen.getByText('Укажите время')).toBeInTheDocument();
    expect(bodies).toEqual([]);
  });

  it('shows the reason the server refused the message', async () => {
    serveCreate(() =>
      HttpResponse.json(
        { code: 'CLUB_NOT_REACHABLE', message: 'Club is not reachable', fields: [] },
        { status: 409 },
      ),
    );
    renderWithProviders(<MessageFormModal clubId={1} onClose={vi.fn()} />);

    await typeIntoEditor('Привет');
    await userEvent.click(screen.getByRole('button', { name: 'Отправить' }));

    expect(
      await screen.findByText('Клуб выключен или у него не указаны чат и топик напоминаний.'),
    ).toBeInTheDocument();
  });

  it('changes only the text of a scheduled message', async () => {
    const message = makeMessage(4, { text: '<b>Привет</b>', send_at: '2026-10-02T16:00:00Z' });
    const bodies = serveUpdate(message);
    renderWithProviders(<MessageFormModal clubId={1} message={message} onClose={vi.fn()} />);

    expect(await screen.findByTestId('reminder-preview')).toHaveTextContent('Привет');
    expect(screen.getByText('02.10.2026 19:00')).toBeInTheDocument();
    await typeIntoEditor('{Control>}a{/Control}Пока');
    await userEvent.click(screen.getByRole('button', { name: 'Запланировать' }));

    await waitFor(() => {
      expect(bodies).toEqual([{ text: 'Пока' }]);
    });
  });

  it('sends a scheduled message right away', async () => {
    const message = makeMessage(4, { send_at: '2026-10-02T16:00:00Z' });
    const bodies = serveUpdate(message);
    renderWithProviders(<MessageFormModal clubId={1} message={message} onClose={vi.fn()} />);

    await userEvent.click(await screen.findByText('Сейчас'));
    await userEvent.click(screen.getByRole('button', { name: 'Отправить' }));

    await waitFor(() => {
      expect(bodies).toEqual([{ send_at: null }]);
    });
  });
});

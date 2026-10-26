import { screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { makeAdmin, makeSettings, meHandler, settingsHandler } from '@/test/fixtures';
import { renderWithProviders } from '@/test/render';
import { server } from '@/test/server';

import { SettingsPage } from './SettingsPage';

const SETTINGS = makeSettings();

describe('SettingsPage', () => {
  it('switches the VK link mode', async () => {
    let body: unknown;
    server.use(
      meHandler(makeAdmin('settings.edit')),
      settingsHandler(SETTINGS),
      http.patch('/api/v1/settings', async ({ request }) => {
        body = await request.json();
        return HttpResponse.json({ ...SETTINGS, vk_link_mode: 'link' });
      }),
    );
    renderWithProviders(<SettingsPage />);

    const form = await screen.findByRole('form', { name: 'Привязка ВК' });
    const save = within(form).getByRole('button', { name: 'Сохранить' });
    expect(save).toBeDisabled();
    await userEvent.click(screen.getByRole('radio', { name: 'Ссылка на страницу' }));
    await userEvent.click(save);

    await waitFor(() => {
      expect(body).toEqual({ vk_link_mode: 'link' });
    });
  });

  it('shows modes without server credentials as unavailable', async () => {
    server.use(
      meHandler(makeAdmin('settings.edit')),
      settingsHandler({ ...SETTINGS, configured_vk_link_modes: ['oauth'] }),
    );
    renderWithProviders(<SettingsPage />);

    expect(
      await screen.findByText('Не настроено на сервере: нужен VK_SERVICE_TOKEN.'),
    ).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: 'Ссылка на страницу' })).toBeDisabled();
  });

  it('changes only the edited default reminder offsets', async () => {
    let body: unknown;
    server.use(
      meHandler(makeAdmin('settings.edit')),
      settingsHandler(SETTINGS),
      http.patch('/api/v1/settings', async ({ request }) => {
        body = await request.json();
        return HttpResponse.json({
          ...SETTINGS,
          default_homework_offsets: [4320, 2880, 1440, 180],
        });
      }),
    );
    renderWithProviders(<SettingsPage />);

    const form = await screen.findByRole('form', { name: 'Новый урок по умолчанию' });
    expect(within(form).getByText('в момент начала')).toBeInTheDocument();
    await userEvent.type(
      within(form).getByLabelText('Напоминания о дедлайне ДЗ: своё значение'),
      '72',
    );
    await userEvent.click(
      within(form).getByRole('button', { name: 'Напоминания о дедлайне ДЗ: добавить' }),
    );
    await userEvent.click(within(form).getByRole('button', { name: 'Сохранить' }));

    await waitFor(() => {
      expect(body).toEqual({ default_homework_offsets: [4320, 2880, 1440, 180] });
    });
  });

  it('is read-only without the settings.edit permission', async () => {
    server.use(meHandler(makeAdmin()), settingsHandler(SETTINGS));
    renderWithProviders(<SettingsPage />);

    expect(await screen.findByRole('radio', { name: 'Вход через VK ID' })).toBeDisabled();
    expect(screen.queryByRole('button', { name: 'Сохранить' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /добавить/ })).not.toBeInTheDocument();
  });

  it('changes the default lesson time', async () => {
    let body: unknown;
    server.use(
      meHandler(makeAdmin('settings.edit')),
      settingsHandler(SETTINGS),
      http.patch('/api/v1/settings', async ({ request }) => {
        body = await request.json();
        return HttpResponse.json({ ...SETTINGS, default_lesson_time: '15:30:00' });
      }),
    );
    renderWithProviders(<SettingsPage />);

    const form = await screen.findByRole('form', { name: 'Новый урок по умолчанию' });
    const time = within(form).getByLabelText('Время начала урока');
    expect(time).toHaveValue('16:00');
    expect(within(form).getByLabelText('Время дедлайна ДЗ')).toHaveValue('23:59');
    await userEvent.clear(time);
    await userEvent.type(time, '15:30');
    await userEvent.click(within(form).getByRole('button', { name: 'Сохранить' }));

    await waitFor(() => {
      expect(body).toEqual({ default_lesson_time: '15:30' });
    });
  });
});

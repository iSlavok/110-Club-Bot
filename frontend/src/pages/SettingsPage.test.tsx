import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import type { AppSettingsResponse } from '@/shared/api';
import { makeAdmin, meHandler } from '@/test/fixtures';
import { renderWithProviders } from '@/test/render';
import { server } from '@/test/server';

import { SettingsPage } from './SettingsPage';

const SETTINGS: AppSettingsResponse = {
  vk_link_mode: 'oauth',
  configured_vk_link_modes: ['link', 'oauth'],
  updated_at: '2026-10-01T09:00:00Z',
};

function settingsHandler(settings: AppSettingsResponse) {
  return http.get('/api/v1/settings', () => HttpResponse.json(settings));
}

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

    const save = await screen.findByRole('button', { name: 'Сохранить' });
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

  it('is read-only without the settings.edit permission', async () => {
    server.use(meHandler(makeAdmin()), settingsHandler(SETTINGS));
    renderWithProviders(<SettingsPage />);

    expect(await screen.findByRole('radio', { name: 'Вход через VK ID' })).toBeDisabled();
    expect(screen.queryByRole('button', { name: 'Сохранить' })).not.toBeInTheDocument();
  });
});

import { screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { makeAdmin, meHandler } from '@/test/fixtures';
import { renderWithProviders } from '@/test/render';
import { server } from '@/test/server';

import { AppLayout } from './AppLayout';

describe('AppLayout', () => {
  it('shows only menu items the admin may open', async () => {
    server.use(meHandler(makeAdmin('clubs.view')));

    renderWithProviders(<AppLayout />);

    expect(await screen.findByText('Тестовый админ')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Обзор' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Клубы' })).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'Пользователи' })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'Админы' })).not.toBeInTheDocument();
  });
});

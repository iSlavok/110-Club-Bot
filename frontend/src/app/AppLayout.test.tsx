import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import type { Permission } from '@/shared/api';
import { clubsHandlers, makeAdmin, makeClub, meHandler } from '@/test/fixtures';
import { renderRoutes } from '@/test/render';
import { server } from '@/test/server';

import { AppLayout } from './AppLayout';

const ROUTES = [{ element: <AppLayout />, children: [{ path: '*', element: <p>page</p> }] }];

function renderAt(route: string, ...permissions: Permission[]) {
  server.use(meHandler(makeAdmin(...permissions)));
  return renderRoutes(ROUTES, { route });
}

function navbar() {
  return within(screen.getByRole('navigation'));
}

describe('AppLayout', () => {
  it('shows only global sections the admin may open', async () => {
    server.use(...clubsHandlers([makeClub(1), makeClub(2)]));

    renderAt('/clubs', 'clubs.view');

    expect(await navbar().findByRole('link', { name: 'Клубы' })).toBeInTheDocument();
    expect(navbar().queryByRole('link', { name: 'Пользователи' })).not.toBeInTheDocument();
    expect(navbar().queryByRole('link', { name: 'Админы' })).not.toBeInTheDocument();
    expect(navbar().queryByRole('link', { name: 'Обзор' })).not.toBeInTheDocument();
  });

  it('inside a club shows its sections and lets switch to another club', async () => {
    server.use(...clubsHandlers([makeClub(7, { title: 'Химия' }), makeClub(8)]));

    renderAt('/clubs/7/blocks', 'clubs.view', 'users.view');

    expect(await navbar().findByRole('link', { name: 'Обзор' })).toHaveAttribute(
      'href',
      '/clubs/7',
    );
    expect(navbar().getByRole('link', { name: 'Блоки' })).toHaveAttribute(
      'href',
      '/clubs/7/blocks',
    );
    expect(navbar().getByRole('link', { name: 'Настройки клуба' })).toBeInTheDocument();
    expect(navbar().getByRole('link', { name: 'Пользователи' })).toBeInTheDocument();

    await userEvent.click(await screen.findByRole('button', { name: 'Сменить клуб' }));
    // Mantine's menu transition leaves items inaccessible to role queries in jsdom; text finds them.
    expect((await screen.findByText('Клуб 8')).closest('a')).toHaveAttribute('href', '/clubs/8');
    expect(screen.getByText('Все клубы').closest('a')).toHaveAttribute('href', '/clubs');
  });

  it('with a single club keeps its sections everywhere and hides the club list', async () => {
    server.use(...clubsHandlers([makeClub(7, { title: 'Химия' })]));

    renderAt('/users', 'clubs.view', 'users.view');

    expect(await navbar().findByRole('link', { name: 'Обзор' })).toHaveAttribute(
      'href',
      '/clubs/7',
    );
    expect(await screen.findByText('Химия')).toBeInTheDocument();
    expect(navbar().queryByRole('link', { name: 'Клубы' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Сменить клуб' })).not.toBeInTheDocument();
  });

  it('without clubs.view shows no club sections', async () => {
    renderAt('/users', 'users.view');

    expect(await navbar().findByRole('link', { name: 'Пользователи' })).toBeInTheDocument();
    expect(navbar().queryByRole('link', { name: 'Обзор' })).not.toBeInTheDocument();
    expect(screen.getByText('Клуб 110')).toBeInTheDocument();
  });
});

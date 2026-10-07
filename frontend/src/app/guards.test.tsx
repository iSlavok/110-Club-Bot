import { screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { makeAdmin, meHandler } from '@/test/fixtures';
import { renderRoutes } from '@/test/render';
import { server } from '@/test/server';

import { RequirePermission, RequireSession } from './guards';

const routes = [
  { path: '/login', element: <p>login page</p> },
  {
    element: <RequireSession />,
    children: [
      {
        path: '/users',
        element: (
          <RequirePermission permission="users.view">
            <p>users page</p>
          </RequirePermission>
        ),
      },
    ],
  },
];

describe('guards', () => {
  it('sends guests to login', async () => {
    server.use(meHandler(null));

    const { router } = renderRoutes(routes, { route: '/users' });

    expect(await screen.findByText('login page')).toBeInTheDocument();
    expect(router.state.location.state).toEqual({ from: '/users' });
  });

  it('hides sections the admin has no permission for', async () => {
    server.use(meHandler(makeAdmin('clubs.view')));

    renderRoutes(routes, { route: '/users' });

    expect(await screen.findByText(/Недостаточно прав/)).toBeInTheDocument();
    expect(screen.queryByText('users page')).not.toBeInTheDocument();
  });

  it('lets permitted admins in', async () => {
    server.use(meHandler(makeAdmin('users.view')));

    renderRoutes(routes, { route: '/users' });

    expect(await screen.findByText('users page')).toBeInTheDocument();
  });
});

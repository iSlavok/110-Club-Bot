import { screen, waitFor } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import type { Permission } from '@/shared/api';
import { clubsHandlers, makeAdmin, makeClub, meHandler } from '@/test/fixtures';
import { renderRoutes } from '@/test/render';
import { server } from '@/test/server';

import { Home } from './Home';

const ROUTES = [
  { path: '/', element: <Home /> },
  { path: '*', element: <p>other page</p> },
];

function renderHome(...permissions: Permission[]) {
  server.use(meHandler(makeAdmin(...permissions)));
  return renderRoutes(ROUTES);
}

describe('Home', () => {
  it('opens the only club right away', async () => {
    server.use(...clubsHandlers([makeClub(7)]));

    const { router } = renderHome('clubs.view');

    await waitFor(() => {
      expect(router.state.location.pathname).toBe('/clubs/7');
    });
  });

  it('opens the club list when there are several clubs', async () => {
    server.use(...clubsHandlers([makeClub(7), makeClub(8)]));

    const { router } = renderHome('clubs.view');

    await waitFor(() => {
      expect(router.state.location.pathname).toBe('/clubs');
    });
  });

  it('opens the first allowed section without clubs.view', async () => {
    const { router } = renderHome('admins.view');

    await waitFor(() => {
      expect(router.state.location.pathname).toBe('/admins');
    });
  });

  it('explains when no section is allowed', async () => {
    renderHome();

    expect(await screen.findByText(/нет доступных разделов/)).toBeInTheDocument();
  });
});

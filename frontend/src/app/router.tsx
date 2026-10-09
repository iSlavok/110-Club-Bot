import type { RouteObject } from 'react-router';

import { AdminsPage } from '@/pages/AdminsPage';
import { ClubBlocksPage } from '@/pages/ClubBlocksPage';
import { ClubOverviewPage } from '@/pages/ClubOverviewPage';
import { ClubSettingsPage } from '@/pages/ClubSettingsPage';
import { ClubsPage } from '@/pages/ClubsPage';
import { LoginPage } from '@/pages/LoginPage';
import { NotFoundPage } from '@/pages/NotFoundPage';
import { RolesPage } from '@/pages/RolesPage';
import { SettingsPage } from '@/pages/SettingsPage';
import { UsersPage } from '@/pages/UsersPage';
import { routes } from '@/shared/config/routes';

import { AppLayout } from './AppLayout';
import { ClubLayout } from './ClubLayout';
import { RequirePermission, RequireSession } from './guards';
import { Home } from './Home';

export const appRoutes: RouteObject[] = [
  { path: routes.login, element: <LoginPage /> },
  {
    element: <RequireSession />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { index: true, element: <Home /> },
          {
            path: routes.clubs,
            element: (
              <RequirePermission permission="clubs.view">
                <ClubsPage />
              </RequirePermission>
            ),
          },
          {
            path: routes.club(':clubId'),
            element: (
              <RequirePermission permission="clubs.view">
                <ClubLayout />
              </RequirePermission>
            ),
            children: [
              { index: true, element: <ClubOverviewPage /> },
              { path: 'blocks', element: <ClubBlocksPage /> },
              { path: 'settings', element: <ClubSettingsPage /> },
            ],
          },
          {
            path: routes.users,
            element: (
              <RequirePermission permission="users.view">
                <UsersPage />
              </RequirePermission>
            ),
          },
          {
            path: routes.admins,
            element: (
              <RequirePermission permission="admins.view">
                <AdminsPage />
              </RequirePermission>
            ),
          },
          {
            path: routes.roles,
            element: (
              <RequirePermission permission="admins.view">
                <RolesPage />
              </RequirePermission>
            ),
          },
          { path: routes.settings, element: <SettingsPage /> },
          { path: '*', element: <NotFoundPage /> },
        ],
      },
    ],
  },
];

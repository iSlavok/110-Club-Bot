import type { RouteObject } from 'react-router';

import { AdminsPage } from '@/pages/AdminsPage';
import { ClubPage } from '@/pages/ClubPage';
import { ClubsPage } from '@/pages/ClubsPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { LoginPage } from '@/pages/LoginPage';
import { NotFoundPage } from '@/pages/NotFoundPage';
import { RolesPage } from '@/pages/RolesPage';
import { UsersPage } from '@/pages/UsersPage';
import { routes } from '@/shared/config/routes';

import { AppLayout } from './AppLayout';
import { RequirePermission, RequireSession } from './guards';

export const appRoutes: RouteObject[] = [
  { path: routes.login, element: <LoginPage /> },
  {
    element: <RequireSession />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { index: true, element: <DashboardPage /> },
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
                <ClubPage />
              </RequirePermission>
            ),
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
          { path: '*', element: <NotFoundPage /> },
        ],
      },
    ],
  },
];

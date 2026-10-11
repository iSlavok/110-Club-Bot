import { Alert, Center, Loader } from '@mantine/core';
import type { ReactNode } from 'react';
import { Navigate, Outlet, useLocation } from 'react-router';

import { useCurrentAdmin, usePermission } from '@/entities/session';
import type { Permission } from '@/shared/api';
import { routes } from '@/shared/config/routes';
import { errorMessage, isUnauthenticated } from '@/shared/lib/errors';

export function RequireSession() {
  const location = useLocation();
  const me = useCurrentAdmin();

  if (me.isPending) {
    return (
      <Center mih="100vh">
        <Loader />
      </Center>
    );
  }
  if (isUnauthenticated(me.error) || !me.data) {
    if (me.error && !isUnauthenticated(me.error)) {
      return (
        <Center mih="100vh" p="md">
          <Alert color="red" title="Админка недоступна">
            {errorMessage(me.error)}
          </Alert>
        </Center>
      );
    }
    return <Navigate to={routes.login} replace state={{ from: location.pathname }} />;
  }
  return <Outlet />;
}

export function RequirePermission({
  permission,
  children,
}: {
  permission: Permission;
  children: ReactNode;
}) {
  if (!usePermission(permission)) {
    return <Alert color="yellow">Недостаточно прав для этого раздела.</Alert>;
  }
  return children;
}

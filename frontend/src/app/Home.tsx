import { Alert, Center, Loader } from '@mantine/core';
import { Navigate } from 'react-router';

import { useClubChoice } from '@/entities/club';
import { hasPermission, useCurrentAdmin } from '@/entities/session';
import { routes } from '@/shared/config/routes';

import { GLOBAL_NAV } from './navigation';

/** `/` has no page of its own: it opens the only club, the club list, or the first section allowed. */
export function Home() {
  const me = useCurrentAdmin().data;
  const canViewClubs = hasPermission(me, 'clubs.view');
  const choice = useClubChoice(canViewClubs);

  if (!canViewClubs) {
    const section = GLOBAL_NAV.find(
      (item) => item.permission && hasPermission(me, item.permission),
    );
    if (!section) {
      return <Alert color="yellow">Для вашей роли пока нет доступных разделов.</Alert>;
    }
    return <Navigate to={section.to} replace />;
  }
  if (choice.isPending) {
    return (
      <Center py="xl">
        <Loader />
      </Center>
    );
  }
  return <Navigate to={choice.onlyClub ? routes.club(choice.onlyClub.id) : routes.clubs} replace />;
}

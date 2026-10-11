import { Center, Loader } from '@mantine/core';
import { Navigate } from 'react-router';

import { useClubChoice } from '@/entities/club';
import { hasPermission, useCurrentAdmin } from '@/entities/session';
import { routes } from '@/shared/config/routes';

import { GLOBAL_NAV } from './navigation';

const loader = (
  <Center py="xl">
    <Loader />
  </Center>
);

/** `/` has no page of its own: it opens the only club, the club list, or the first section allowed. */
export function Home() {
  const me = useCurrentAdmin().data;
  const canViewClubs = hasPermission(me, 'clubs.view');
  const choice = useClubChoice(canViewClubs);

  if (!me) {
    return loader;
  }
  if (!canViewClubs) {
    // The bot settings section needs no permission, so every admin has somewhere to go.
    const section = GLOBAL_NAV.find(
      (item) => !item.permission || hasPermission(me, item.permission),
    );
    return <Navigate to={section?.to ?? routes.settings} replace />;
  }
  if (choice.isPending) {
    return loader;
  }
  return <Navigate to={choice.onlyClub ? routes.club(choice.onlyClub.id) : routes.clubs} replace />;
}

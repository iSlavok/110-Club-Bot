import { Outlet } from 'react-router';

import { useGetClub } from '@/shared/api';
import { useClubId } from '@/shared/lib/club-id';
import { QueryState } from '@/shared/ui/QueryState';

/** Club pages render only for a club that exists; an unknown id shows the error once, here. */
export function ClubLayout() {
  const club = useGetClub(useClubId());
  return (
    <QueryState data={club.data} error={club.error} isPending={club.isPending}>
      {() => <Outlet />}
    </QueryState>
  );
}

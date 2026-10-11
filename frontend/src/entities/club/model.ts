import { useListClubs, type ClubResponse } from '@/shared/api';

// The API cap for one page; a school runs a handful of clubs, so one page is all of them.
const ALL_CLUBS = { per_page: 200 };

export interface ClubChoice {
  clubs: ClubResponse[];
  isPending: boolean;
  /** The club everything opens into when it is the only one, otherwise null. */
  onlyClub: ClubResponse | null;
}

export function useClubChoice(enabled: boolean): ClubChoice {
  const query = useListClubs(ALL_CLUBS, { query: { enabled, staleTime: 60_000 } });
  const clubs = query.data?.items ?? [];
  return {
    clubs,
    isPending: enabled && query.isPending,
    onlyClub: query.data?.total_items === 1 ? (clubs[0] ?? null) : null,
  };
}

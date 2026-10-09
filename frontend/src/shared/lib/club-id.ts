import { useMatch, useParams } from 'react-router';

/** Club of a page under `/clubs/:clubId/…`; the router guarantees the param there. */
export function useClubId(): number {
  return Number(useParams().clubId);
}

/** Club in the URL from anywhere in the layout, or null outside club pages. */
export function useRouteClubId(): number | null {
  const match = useMatch({ path: '/clubs/:clubId', end: false });
  const clubId = Number(match?.params.clubId);
  return Number.isInteger(clubId) && clubId > 0 ? clubId : null;
}

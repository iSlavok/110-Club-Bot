import { MutationCache, QueryCache, QueryClient } from '@tanstack/react-query';

import { ApiError, getGetMeQueryKey } from '@/shared/api';
import { isUnauthenticated } from '@/shared/lib/errors';

const ME_KEY = getGetMeQueryKey()[0];

export function createQueryClient(): QueryClient {
  const queryClient: QueryClient = new QueryClient({
    // An expired session surfaces as 401 on any request: refetching /me lets the guard send the user to login.
    queryCache: new QueryCache({
      onError: (error, query) => {
        if (isUnauthenticated(error) && query.queryKey[0] !== ME_KEY) {
          void queryClient.invalidateQueries({ queryKey: getGetMeQueryKey() });
        }
      },
    }),
    // Admin data is small and interlinked, so every successful change simply refreshes what is on screen.
    mutationCache: new MutationCache({
      onSuccess: (_data, _variables, _context, mutation) => {
        if (mutation.options.mutationKey?.[0] !== 'logout') {
          void queryClient.invalidateQueries({
            predicate: (query) => query.queryKey[0] !== ME_KEY,
          });
        }
      },
    }),
    defaultOptions: {
      queries: {
        retry: (failureCount, error) =>
          !(error instanceof ApiError && error.status < 500) && failureCount < 2,
        refetchOnWindowFocus: false,
      },
    },
  });
  return queryClient;
}

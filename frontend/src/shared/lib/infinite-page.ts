import { keepPreviousData } from '@tanstack/react-query';
import { useCallback, useMemo } from 'react';

export const PER_PAGE = 50;

interface PageMeta {
  page: number;
  total_pages: number;
}

interface PageOf<T> extends PageMeta {
  items: T[];
  total_items: number;
}

/** Query options for orval's `use…Infinite` hooks over `Page[T]` endpoints. */
export const infinitePage = {
  query: {
    initialPageParam: 1,
    getNextPageParam: (last: PageMeta) =>
      last.page < last.total_pages ? last.page + 1 : undefined,
    // Changing a filter keeps the old rows on screen until the new first page arrives.
    placeholderData: keepPreviousData,
  },
};

interface InfiniteQueryLike<T> {
  data: { pages: PageOf<T>[] } | undefined;
  error: unknown;
  isPending: boolean;
  hasNextPage: boolean;
  isFetchingNextPage: boolean;
  isFetchNextPageError: boolean;
  fetchNextPage: () => Promise<unknown>;
}

interface ListQueryLike<T> {
  data: T[] | undefined;
  error: unknown;
  isPending: boolean;
}

/** What `InfiniteList` renders: loaded rows plus the state of loading the rest. */
export interface InfinitePage<T> {
  items: T[];
  total: number | undefined;
  isPending: boolean;
  error: unknown;
  hasNextPage: boolean;
  isFetchingNextPage: boolean;
  isFetchNextPageError: boolean;
  fetchNextPage: () => void;
}

/**
 * Flattens an orval infinite query for `InfiniteList`. Call the generated hook on its own line:
 * nested inside this call, TypeScript infers the hook's data type from here and loses the item type.
 */
export function useInfinitePage<T>(query: InfiniteQueryLike<T>): InfinitePage<T> {
  const { data, error, isPending, hasNextPage, isFetchingNextPage, isFetchNextPageError } = query;
  const { fetchNextPage } = query;
  const items = useMemo(() => data?.pages.flatMap((page) => page.items) ?? [], [data]);
  const loadMore = useCallback(() => {
    void fetchNextPage();
  }, [fetchNextPage]);
  return {
    items,
    total: data?.pages[0]?.total_items,
    isPending,
    // A failed next page keeps the loaded rows; InfiniteList shows its error below them.
    error: isFetchNextPageError ? null : error,
    hasNextPage,
    isFetchingNextPage,
    isFetchNextPageError,
    fetchNextPage: loadMore,
  };
}

/** A short list the API returns whole (roles) in the same `InfiniteList` look. */
export function wholeList<T>(query: ListQueryLike<T>): InfinitePage<T> {
  const { data, error, isPending } = query;
  return {
    items: data ?? [],
    total: data?.length,
    isPending,
    error,
    hasNextPage: false,
    isFetchingNextPage: false,
    isFetchNextPageError: false,
    fetchNextPage: () => undefined,
  };
}

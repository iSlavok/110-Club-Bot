import { Alert, Button, Center, Group, Loader, Stack, Text } from '@mantine/core';
import { useEffect, useRef, type ReactNode } from 'react';

import { errorMessage } from '@/shared/lib/errors';
import type { InfinitePage } from '@/shared/lib/infinite-page';

interface InfiniteListProps<T> {
  list: InfinitePage<T>;
  /** Filters and sorting above the list; stays mounted while the list reloads. */
  filters?: ReactNode;
  emptyText: string;
  children: (items: T[]) => ReactNode;
}

export function InfiniteList<T>({ list, filters, emptyText, children }: InfiniteListProps<T>) {
  return (
    <Stack gap="md">
      {filters && (
        <Group gap="sm" align="flex-end" wrap="wrap">
          {filters}
        </Group>
      )}
      <ListBody list={list} emptyText={emptyText}>
        {children}
      </ListBody>
    </Stack>
  );
}

function ListBody<T>({ list, emptyText, children }: Omit<InfiniteListProps<T>, 'filters'>) {
  if (list.isPending) {
    return (
      <Center py="xl">
        <Loader />
      </Center>
    );
  }
  if (list.error) {
    return (
      <Alert color="red" title="Не удалось загрузить данные">
        {errorMessage(list.error)}
      </Alert>
    );
  }
  if (list.items.length === 0) {
    return (
      <Text c="dimmed" ta="center" py="xl">
        {emptyText}
      </Text>
    );
  }
  return (
    <>
      {children(list.items)}
      <ListEnd list={list} />
    </>
  );
}

function ListEnd<T>({ list }: { list: InfinitePage<T> }) {
  const { hasNextPage, isFetchingNextPage, isFetchNextPageError, fetchNextPage } = list;
  const sentinel = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const node = sentinel.current;
    if (!node || !hasNextPage || isFetchingNextPage || isFetchNextPageError) {
      return;
    }
    // Re-created after every page: if the end is still in view, the next page loads right away.
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          fetchNextPage();
        }
      },
      { rootMargin: '300px' },
    );
    observer.observe(node);
    return () => {
      observer.disconnect();
    };
  }, [hasNextPage, isFetchingNextPage, isFetchNextPageError, fetchNextPage]);

  return (
    <div ref={sentinel}>
      {isFetchingNextPage && (
        <Center py="md">
          <Loader size="sm" aria-label="Загрузка ещё" />
        </Center>
      )}
      {isFetchNextPageError && (
        <Center py="md">
          <Button variant="light" color="red" onClick={fetchNextPage}>
            Не удалось загрузить ещё. Повторить
          </Button>
        </Center>
      )}
      {!hasNextPage && list.total !== undefined && (
        <Text size="sm" c="dimmed" ta="center" py="sm">
          Всего: {list.total}
        </Text>
      )}
    </div>
  );
}

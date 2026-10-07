import { Group, Pagination, Text } from '@mantine/core';

import type { PageState } from '@/shared/lib/use-page';

interface TablePaginationProps {
  state: PageState;
  result: { total_items: number; total_pages: number };
}

export function TablePagination({ state, result }: TablePaginationProps) {
  return (
    <Group justify="space-between" mt="md">
      <Text size="sm" c="dimmed">
        Всего: {result.total_items}
      </Text>
      {result.total_pages > 1 && (
        <Pagination value={state.page} onChange={state.setPage} total={result.total_pages} />
      )}
    </Group>
  );
}

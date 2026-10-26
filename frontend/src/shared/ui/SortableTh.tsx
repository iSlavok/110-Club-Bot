import { Group, Table, UnstyledButton } from '@mantine/core';
import { IconChevronDown, IconChevronUp, IconSelector } from '@tabler/icons-react';
import type { ReactNode } from 'react';

import type { SortOrder } from '@/shared/api';

interface SortableThProps<Sort extends string> {
  sort: Sort;
  current: { sort: Sort; order: SortOrder };
  onSort: (next: { sort: Sort; order: SortOrder }) => void;
  w?: number;
  children: ReactNode;
}

/** A header that sorts by its column; pressing the active one again reverses the order. */
export function SortableTh<Sort extends string>({
  sort,
  current,
  onSort,
  w,
  children,
}: SortableThProps<Sort>) {
  const active = current.sort === sort;
  const Icon = !active ? IconSelector : current.order === 'asc' ? IconChevronUp : IconChevronDown;
  return (
    <Table.Th
      w={w}
      aria-sort={active ? (current.order === 'asc' ? 'ascending' : 'descending') : 'none'}
    >
      <UnstyledButton
        fw={700}
        fz="sm"
        onClick={() => {
          onSort({ sort, order: active && current.order === 'asc' ? 'desc' : 'asc' });
        }}
      >
        <Group gap={4} wrap="nowrap">
          {children}
          <Icon size={14} stroke={1.5} />
        </Group>
      </UnstyledButton>
    </Table.Th>
  );
}

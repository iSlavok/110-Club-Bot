import { Badge } from '@mantine/core';

import type { BlockResponse } from '@/shared/api';

export function blockStatus(block: BlockResponse, now: Date): 'upcoming' | 'current' | 'finished' {
  if (now < new Date(block.starts_at)) {
    return 'upcoming';
  }
  return now < new Date(block.ends_at) ? 'current' : 'finished';
}

const LABELS = {
  upcoming: { color: 'blue', label: 'Скоро' },
  current: { color: 'teal', label: 'Идёт' },
  finished: { color: 'gray', label: 'Завершён' },
} as const;

export function BlockStatusBadge({ block }: { block: BlockResponse }) {
  const { color, label } = LABELS[blockStatus(block, new Date())];
  return (
    <Badge color={color} variant="light">
      {label}
    </Badge>
  );
}

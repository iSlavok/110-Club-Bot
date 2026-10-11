import { Badge } from '@mantine/core';

import type { ReminderStatus } from '@/shared/api';

import { REMINDER_STATUSES } from './labels';

export function ReminderStatusBadge({ status }: { status: ReminderStatus }) {
  const { label, color } = REMINDER_STATUSES[status];
  return (
    <Badge color={color} variant="light">
      {label}
    </Badge>
  );
}

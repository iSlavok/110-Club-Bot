import { Badge, Text } from '@mantine/core';

import type { SheetSyncResponse, SheetSyncStatus } from '@/shared/api';

const LABELS = {
  ok: { color: 'teal', label: 'Успешно' },
  failed: { color: 'red', label: 'Ошибка' },
} as const;

export function SyncStatusBadge({ status }: { status: SheetSyncStatus }) {
  const { color, label } = LABELS[status];
  return (
    <Badge color={color} variant="light">
      {label}
    </Badge>
  );
}

/** Joined straight away; the gone ones wait for the owner's confirmation in the alerts chat. */
export function SyncChanges({ sync }: { sync: SheetSyncResponse }) {
  return (
    <Text span size="sm">
      <Text span c="teal.7">
        +{sync.added}
      </Text>
      {sync.removal_requested > 0 && (
        <Text span c="orange.7">
          {' '}
          · на удаление: {sync.removal_requested}
        </Text>
      )}
    </Text>
  );
}

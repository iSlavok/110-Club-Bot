import { Badge, Tooltip } from '@mantine/core';

import { formatDateTime } from '@/shared/lib/dates';

export function BotBlockedBadge({ blockedAt }: { blockedAt: string }) {
  return (
    <Tooltip label={`Заблокировал бота ${formatDateTime(blockedAt)}`}>
      <Badge color="red" variant="light">
        заблокировал бота
      </Badge>
    </Tooltip>
  );
}

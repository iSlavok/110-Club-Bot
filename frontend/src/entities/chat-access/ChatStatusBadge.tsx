import { Badge } from '@mantine/core';

import type { ChatAccessStatus } from '@/shared/api';

const CHAT_STATUSES: Record<ChatAccessStatus, { label: string; color: string }> = {
  invited: { label: 'приглашён', color: 'yellow' },
  joined: { label: 'в чате', color: 'green' },
  left: { label: 'вышел', color: 'gray' },
  kicked: { label: 'удалён', color: 'red' },
};

export function ChatStatusBadge({ status }: { status: ChatAccessStatus }) {
  const { label, color } = CHAT_STATUSES[status];
  return (
    <Badge color={color} variant="light">
      {label}
    </Badge>
  );
}

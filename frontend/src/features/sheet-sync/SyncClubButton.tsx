import { Button } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconRefresh } from '@tabler/icons-react';

import { useSyncClub, type SheetSyncResponse } from '@/shared/api';
import { notifyError } from '@/shared/lib/notify';

function notifyResult(sync: SheetSyncResponse): void {
  if (sync.status === 'failed') {
    notifications.show({
      color: 'red',
      title: 'Таблицу прочитать не удалось',
      message: sync.error ?? 'Неизвестная ошибка',
    });
    return;
  }
  const parts = [`добавлено ${sync.added}`];
  if (sync.removal_requested > 0) {
    parts.push(`на подтверждение удаления: ${sync.removal_requested}`);
  }
  if (sync.issues.length > 0) {
    parts.push(`проблем в таблице: ${sync.issues.length}`);
  }
  notifications.show({
    color: sync.issues.length > 0 ? 'yellow' : 'teal',
    message: `Синк выполнен: ${parts.join(', ')}`,
  });
}

export function SyncClubButton({ clubId, disabled }: { clubId: number; disabled?: boolean }) {
  const sync = useSyncClub({ mutation: { onSuccess: notifyResult, onError: notifyError } });
  return (
    <Button
      leftSection={<IconRefresh size={16} />}
      loading={sync.isPending}
      disabled={disabled}
      onClick={() => {
        sync.mutate({ clubId });
      }}
    >
      Синхронизировать
    </Button>
  );
}

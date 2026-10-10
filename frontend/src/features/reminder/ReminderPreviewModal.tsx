import { Modal, Paper } from '@mantine/core';

import { usePreviewReminder } from '@/shared/api';
import { QueryState } from '@/shared/ui/QueryState';

interface ReminderPreviewModalProps {
  reminderId: number;
  onClose: () => void;
}

export function ReminderPreviewModal({ reminderId, onClose }: ReminderPreviewModalProps) {
  const preview = usePreviewReminder(reminderId);
  return (
    <Modal opened onClose={onClose} title="Текст напоминания" size="lg">
      <QueryState data={preview.data} error={preview.error} isPending={preview.isPending}>
        {(data) => (
          <Paper withBorder p="md" radius="md" bg="var(--mantine-color-default-hover)">
            {/* Safe to inject: the backend escapes every admin-entered field, the only tags are its own. */}
            <div
              data-testid="reminder-preview"
              style={{ whiteSpace: 'pre-wrap' }}
              dangerouslySetInnerHTML={{ __html: data.html }}
            />
          </Paper>
        )}
      </QueryState>
    </Modal>
  );
}

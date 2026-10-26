import { Modal } from '@mantine/core';

import { ReminderMessage } from '@/entities/reminder';
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
        {(data) => <ReminderMessage html={data.html} />}
      </QueryState>
    </Modal>
  );
}

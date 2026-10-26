import { Modal } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';

import { previewDraftReminder, type ReminderDraftPreview } from '@/shared/api';
import { QueryState } from '@/shared/ui/QueryState';

import { ReminderMessage } from './ReminderMessage';

// A POST only because the draft is a body; nothing is saved, so it is cached like a read.
export function DraftReminderPreview({ request }: { request: ReminderDraftPreview }) {
  const preview = useQuery({
    queryKey: ['reminder-draft-preview', request],
    queryFn: () => previewDraftReminder(request),
  });
  return (
    <QueryState data={preview.data} error={preview.error} isPending={preview.isPending}>
      {(data) => <ReminderMessage html={data.html} />}
    </QueryState>
  );
}

interface DraftReminderPreviewModalProps {
  title: string;
  request: ReminderDraftPreview;
  onClose: () => void;
}

export function DraftReminderPreviewModal({
  title,
  request,
  onClose,
}: DraftReminderPreviewModalProps) {
  return (
    <Modal opened onClose={onClose} title={title} size="lg">
      <DraftReminderPreview request={request} />
    </Modal>
  );
}

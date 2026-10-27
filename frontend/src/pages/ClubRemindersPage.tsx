import { Button } from '@mantine/core';
import { IconMessagePlus } from '@tabler/icons-react';
import { useState } from 'react';

import { Can } from '@/entities/session';
import { MessageFormModal, ReminderFeed } from '@/features/reminder';
import { useClubId } from '@/shared/lib/club-id';
import { PageHeader } from '@/shared/ui/PageHeader';

export function ClubRemindersPage() {
  const clubId = useClubId();
  const [writing, setWriting] = useState(false);
  return (
    <>
      <PageHeader
        title="Напоминания"
        actions={
          <Can permission="messages.send">
            <Button
              leftSection={<IconMessagePlus size={16} />}
              onClick={() => {
                setWriting(true);
              }}
            >
              Сообщение в чат
            </Button>
          </Can>
        }
      />
      <ReminderFeed clubId={clubId} />
      {writing && (
        <MessageFormModal
          clubId={clubId}
          onClose={() => {
            setWriting(false);
          }}
        />
      )}
    </>
  );
}

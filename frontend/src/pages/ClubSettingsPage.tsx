import { Badge, Button, Paper, SimpleGrid, Text } from '@mantine/core';
import { IconPencil } from '@tabler/icons-react';
import { useState } from 'react';

import { Can } from '@/entities/session';
import { ClubFormModal } from '@/features/club';
import { useGetClub, type ClubResponse } from '@/shared/api';
import { useClubId } from '@/shared/lib/club-id';
import { PageHeader } from '@/shared/ui/PageHeader';
import { QueryState } from '@/shared/ui/QueryState';

function Field({ label, value }: { label: string; value: string | number | null }) {
  return (
    <div>
      <Text size="xs" c="dimmed">
        {label}
      </Text>
      <Text>{value ?? '—'}</Text>
    </div>
  );
}

function ClubSettings({ club }: { club: ClubResponse }) {
  const [editing, setEditing] = useState(false);
  return (
    <>
      <PageHeader
        title="Настройки клуба"
        actions={
          <Can permission="clubs.edit">
            <Button
              variant="default"
              leftSection={<IconPencil size={16} />}
              onClick={() => {
                setEditing(true);
              }}
            >
              Изменить
            </Button>
          </Can>
        }
      />
      <Paper withBorder radius="md" p="md">
        <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }}>
          <Field label="Название" value={club.title} />
          <Field label="ID чата" value={club.chat_id} />
          <Field label="Топик напоминаний" value={club.reminders_topic_id} />
          <Field label="Google-таблица" value={club.spreadsheet_id} />
          <Field label="Лист" value={club.sheet_name} />
          <div>
            <Text size="xs" c="dimmed">
              Статус
            </Text>
            <Badge color={club.is_active ? 'teal' : 'gray'} variant="light">
              {club.is_active ? 'Активен' : 'Выключен'}
            </Badge>
          </div>
        </SimpleGrid>
      </Paper>
      {editing && (
        <ClubFormModal
          opened
          club={club}
          onClose={() => {
            setEditing(false);
          }}
        />
      )}
    </>
  );
}

export function ClubSettingsPage() {
  const club = useGetClub(useClubId());
  return (
    <QueryState data={club.data} error={club.error} isPending={club.isPending}>
      {(data) => <ClubSettings club={data} />}
    </QueryState>
  );
}

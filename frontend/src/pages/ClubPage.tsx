import {
  ActionIcon,
  Badge,
  Button,
  Group,
  Paper,
  SimpleGrid,
  Table,
  Text,
  Title,
} from '@mantine/core';
import { IconPencil, IconPlus, IconTrash } from '@tabler/icons-react';
import { useState } from 'react';
import { useParams } from 'react-router';

import { BlockStatusBadge } from '@/entities/block';
import { Can } from '@/entities/session';
import { BlockFormModal, useDeleteBlockConfirm } from '@/features/block';
import { ClubFormModal } from '@/features/club';
import { useGetClub, useListBlocks, type BlockResponse, type ClubResponse } from '@/shared/api';
import { formatDateTime } from '@/shared/lib/dates';
import { usePage } from '@/shared/lib/use-page';
import { PageHeader } from '@/shared/ui/PageHeader';
import { QueryState } from '@/shared/ui/QueryState';
import { TablePagination } from '@/shared/ui/TablePagination';

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

function ClubDetails({ club }: { club: ClubResponse }) {
  const [editing, setEditing] = useState(false);
  return (
    <>
      <PageHeader
        title={
          <Group gap="sm">
            {club.title}
            {!club.is_active && <Badge color="gray">Выключен</Badge>}
          </Group>
        }
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
      <Paper withBorder radius="md" p="md" mb="xl">
        <SimpleGrid cols={{ base: 1, sm: 2, md: 4 }}>
          <Field label="ID чата" value={club.chat_id} />
          <Field label="Топик напоминаний" value={club.reminders_topic_id} />
          <Field label="Google-таблица" value={club.spreadsheet_id} />
          <Field label="Лист" value={club.sheet_name} />
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

function Blocks({ clubId }: { clubId: number }) {
  const page = usePage();
  const blocks = useListBlocks(clubId, page.params);
  const [editing, setEditing] = useState<BlockResponse | 'new' | null>(null);
  const confirmDelete = useDeleteBlockConfirm();

  return (
    <>
      <Group justify="space-between" mb="sm">
        <Title order={3}>Блоки</Title>
        <Can permission="blocks.edit">
          <Button
            leftSection={<IconPlus size={16} />}
            onClick={() => {
              setEditing('new');
            }}
          >
            Новый блок
          </Button>
        </Can>
      </Group>
      <QueryState data={blocks.data} error={blocks.error} isPending={blocks.isPending}>
        {(data) => (
          <>
            <Table.ScrollContainer minWidth={700}>
              <Table verticalSpacing="sm">
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Название</Table.Th>
                    <Table.Th>Столбец таблицы</Table.Th>
                    <Table.Th>Начало (МСК)</Table.Th>
                    <Table.Th>Конец (МСК)</Table.Th>
                    <Table.Th>Статус</Table.Th>
                    <Table.Th />
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {data.items.map((block) => (
                    <Table.Tr key={block.id}>
                      <Table.Td fw={500}>{block.title}</Table.Td>
                      <Table.Td>{block.sheet_column_title}</Table.Td>
                      <Table.Td>{formatDateTime(block.starts_at)}</Table.Td>
                      <Table.Td>{formatDateTime(block.ends_at)}</Table.Td>
                      <Table.Td>
                        <BlockStatusBadge block={block} />
                      </Table.Td>
                      <Table.Td>
                        <Can permission="blocks.edit">
                          <Group gap={4} justify="flex-end" wrap="nowrap">
                            <ActionIcon
                              variant="subtle"
                              aria-label="Изменить блок"
                              onClick={() => {
                                setEditing(block);
                              }}
                            >
                              <IconPencil size={18} />
                            </ActionIcon>
                            <ActionIcon
                              variant="subtle"
                              color="red"
                              aria-label="Удалить блок"
                              onClick={() => {
                                confirmDelete(block);
                              }}
                            >
                              <IconTrash size={18} />
                            </ActionIcon>
                          </Group>
                        </Can>
                      </Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            </Table.ScrollContainer>
            {data.items.length === 0 && (
              <Text c="dimmed" ta="center" py="xl">
                Блоков пока нет
              </Text>
            )}
            <TablePagination state={page} result={data} />
          </>
        )}
      </QueryState>
      {editing && (
        <BlockFormModal
          opened
          key={editing === 'new' ? 'new' : editing.id}
          clubId={clubId}
          block={editing === 'new' ? undefined : editing}
          onClose={() => {
            setEditing(null);
          }}
        />
      )}
    </>
  );
}

export function ClubPage() {
  const clubId = Number(useParams().clubId);
  const club = useGetClub(clubId);
  return (
    <QueryState data={club.data} error={club.error} isPending={club.isPending}>
      {(data) => (
        <>
          <ClubDetails club={data} />
          <Blocks clubId={data.id} />
        </>
      )}
    </QueryState>
  );
}

import { ActionIcon, Button, Group, Table, UnstyledButton } from '@mantine/core';
import { IconPencil, IconPlus, IconTrash } from '@tabler/icons-react';
import { useState } from 'react';

import { BlockStatusBadge } from '@/entities/block';
import { Can, usePermission } from '@/entities/session';
import { BlockFormModal, BlockMembersModal, useDeleteBlockConfirm } from '@/features/block';
import {
  useListBlocksInfinite,
  type BlockListItemResponse,
  type BlockResponse,
} from '@/shared/api';
import { useClubId } from '@/shared/lib/club-id';
import { formatDateTime } from '@/shared/lib/dates';
import { infinitePage, PER_PAGE, useInfinitePage } from '@/shared/lib/infinite-page';
import { InfiniteList } from '@/shared/ui/InfiniteList';
import { PageHeader } from '@/shared/ui/PageHeader';

function MembersCount({ block, onOpen }: { block: BlockListItemResponse; onOpen: () => void }) {
  const canViewMembers = usePermission('users.view');
  if (!canViewMembers) {
    return <>{block.members_count}</>;
  }
  return (
    <UnstyledButton
      c="blue"
      td="underline"
      aria-label={`Участники блока ${block.title}`}
      onClick={onOpen}
    >
      {block.members_count}
    </UnstyledButton>
  );
}

export function ClubBlocksPage() {
  const clubId = useClubId();
  const query = useListBlocksInfinite(clubId, { per_page: PER_PAGE }, infinitePage);
  const blocks = useInfinitePage(query);
  const [editing, setEditing] = useState<BlockResponse | 'new' | null>(null);
  const [viewingMembers, setViewingMembers] = useState<BlockResponse | null>(null);
  const confirmDelete = useDeleteBlockConfirm();

  return (
    <>
      <PageHeader
        title="Блоки"
        actions={
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
        }
      />
      <InfiniteList list={blocks} emptyText="Блоков пока нет">
        {(items) => (
          <Table.ScrollContainer minWidth={700}>
            <Table verticalSpacing="sm">
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Название</Table.Th>
                  <Table.Th>Столбец таблицы</Table.Th>
                  <Table.Th>Начало (МСК)</Table.Th>
                  <Table.Th>Конец (МСК)</Table.Th>
                  <Table.Th>Статус</Table.Th>
                  <Table.Th>Участников</Table.Th>
                  <Table.Th />
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {items.map((block) => (
                  <Table.Tr key={block.id}>
                    <Table.Td fw={500}>{block.title}</Table.Td>
                    <Table.Td>{block.sheet_column_title}</Table.Td>
                    <Table.Td>{formatDateTime(block.starts_at)}</Table.Td>
                    <Table.Td>{formatDateTime(block.ends_at)}</Table.Td>
                    <Table.Td>
                      <BlockStatusBadge block={block} />
                    </Table.Td>
                    <Table.Td>
                      <MembersCount
                        block={block}
                        onOpen={() => {
                          setViewingMembers(block);
                        }}
                      />
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
        )}
      </InfiniteList>
      {viewingMembers && (
        <BlockMembersModal
          opened
          key={viewingMembers.id}
          block={viewingMembers}
          onClose={() => {
            setViewingMembers(null);
          }}
        />
      )}
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

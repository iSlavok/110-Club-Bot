import { ActionIcon, Badge, Button, Group, Table, Text } from '@mantine/core';
import { IconPencil, IconPlus } from '@tabler/icons-react';
import { useState } from 'react';

import { Can, canGrant, useCurrentAdmin, usePermission } from '@/entities/session';
import { AdminFormModal } from '@/features/admin';
import { useListAdminsInfinite, useListRoles, type AdminUserResponse } from '@/shared/api';
import { infinitePage, PER_PAGE, useInfinitePage } from '@/shared/lib/infinite-page';
import { InfiniteList } from '@/shared/ui/InfiniteList';
import { PageHeader } from '@/shared/ui/PageHeader';

export function AdminsPage() {
  const query = useListAdminsInfinite({ per_page: PER_PAGE }, infinitePage);
  const admins = useInfinitePage(query);
  const roles = useListRoles();
  const me = useCurrentAdmin().data;
  const canEdit = usePermission('admins.edit');
  const [editing, setEditing] = useState<AdminUserResponse | 'new' | null>(null);

  const assignableRoles = (roles.data ?? []).filter((role) => canGrant(me, role.permissions));
  const isEditable = (admin: AdminUserResponse) =>
    canEdit &&
    !admin.is_owner &&
    admin.id !== me?.id &&
    canGrant(me, roles.data?.find((role) => role.id === admin.role?.id)?.permissions ?? []);

  return (
    <>
      <PageHeader
        title="Админы"
        actions={
          <Can permission="admins.edit">
            <Button
              leftSection={<IconPlus size={16} />}
              onClick={() => {
                setEditing('new');
              }}
            >
              Добавить
            </Button>
          </Can>
        }
      />
      <InfiniteList list={admins} emptyText="Админов пока нет">
        {(items) => (
          <Table.ScrollContainer minWidth={600}>
            <Table verticalSpacing="sm">
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Имя</Table.Th>
                  <Table.Th>Telegram id</Table.Th>
                  <Table.Th>Роль</Table.Th>
                  <Table.Th>Статус</Table.Th>
                  <Table.Th />
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {items.map((admin) => (
                  <Table.Tr key={admin.id}>
                    <Table.Td fw={500}>{admin.name}</Table.Td>
                    <Table.Td>{admin.tg_id}</Table.Td>
                    <Table.Td>
                      {admin.is_owner ? (
                        <Badge color="grape">Владелец</Badge>
                      ) : (
                        (admin.role?.title ?? <Text c="dimmed">—</Text>)
                      )}
                    </Table.Td>
                    <Table.Td>
                      <Badge color={admin.is_active ? 'teal' : 'gray'} variant="light">
                        {admin.is_active ? 'Активен' : 'Отключён'}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      {isEditable(admin) && (
                        <Group justify="flex-end">
                          <ActionIcon
                            variant="subtle"
                            aria-label="Изменить админа"
                            onClick={() => {
                              setEditing(admin);
                            }}
                          >
                            <IconPencil size={18} />
                          </ActionIcon>
                        </Group>
                      )}
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Table.ScrollContainer>
        )}
      </InfiniteList>
      {editing && (
        <AdminFormModal
          opened
          key={editing === 'new' ? 'new' : editing.id}
          roles={assignableRoles}
          admin={editing === 'new' ? undefined : editing}
          onClose={() => {
            setEditing(null);
          }}
        />
      )}
    </>
  );
}

import { ActionIcon, Badge, Button, Group, Paper, Stack, Text } from '@mantine/core';
import { IconPencil, IconPlus, IconTrash } from '@tabler/icons-react';
import { useState } from 'react';

import { Can, canGrant, useCurrentAdmin, usePermission } from '@/entities/session';
import { RoleFormModal, useDeleteRoleConfirm } from '@/features/role';
import { useListPermissions, useListRoles, type RoleResponse } from '@/shared/api';
import { PageHeader } from '@/shared/ui/PageHeader';
import { QueryState } from '@/shared/ui/QueryState';

export function RolesPage() {
  const roles = useListRoles();
  const catalog = useListPermissions();
  const me = useCurrentAdmin().data;
  const canEdit = usePermission('roles.edit');
  const confirmDelete = useDeleteRoleConfirm();
  const [editing, setEditing] = useState<RoleResponse | 'new' | null>(null);

  const titles = new Map(catalog.data?.map((permission) => [permission.code, permission.title]));

  return (
    <>
      <PageHeader
        title="Роли"
        actions={
          <Can permission="roles.edit">
            <Button
              leftSection={<IconPlus size={16} />}
              onClick={() => {
                setEditing('new');
              }}
            >
              Новая роль
            </Button>
          </Can>
        }
      />
      <QueryState data={roles.data} error={roles.error} isPending={roles.isPending}>
        {(data) => (
          <Stack>
            {data.map((role) => (
              <Paper key={role.id} withBorder radius="md" p="md">
                <Group justify="space-between" align="flex-start" wrap="nowrap">
                  <Stack gap="xs">
                    <Text fw={600}>{role.title}</Text>
                    <Group gap={6}>
                      {role.permissions.length === 0 && (
                        <Text size="sm" c="dimmed">
                          Без прав
                        </Text>
                      )}
                      {role.permissions.map((permission) => (
                        <Badge key={permission} variant="light">
                          {titles.get(permission) ?? permission}
                        </Badge>
                      ))}
                    </Group>
                  </Stack>
                  {canEdit && canGrant(me, role.permissions) && (
                    <Group gap={4} wrap="nowrap">
                      <ActionIcon
                        variant="subtle"
                        aria-label="Изменить роль"
                        onClick={() => {
                          setEditing(role);
                        }}
                      >
                        <IconPencil size={18} />
                      </ActionIcon>
                      <ActionIcon
                        variant="subtle"
                        color="red"
                        aria-label="Удалить роль"
                        onClick={() => {
                          confirmDelete(role);
                        }}
                      >
                        <IconTrash size={18} />
                      </ActionIcon>
                    </Group>
                  )}
                </Group>
              </Paper>
            ))}
            {data.length === 0 && (
              <Text c="dimmed" ta="center" py="xl">
                Ролей пока нет
              </Text>
            )}
          </Stack>
        )}
      </QueryState>
      {editing && catalog.data && (
        <RoleFormModal
          opened
          key={editing === 'new' ? 'new' : editing.id}
          catalog={catalog.data}
          grantable={me?.permissions ?? []}
          role={editing === 'new' ? undefined : editing}
          onClose={() => {
            setEditing(null);
          }}
        />
      )}
    </>
  );
}

import { Button, Checkbox, Group, Modal, Stack, Text, TextInput } from '@mantine/core';
import { useForm } from '@mantine/form';

import { groupPermissions, PERMISSION_GROUP_TITLES } from '@/entities/role';
import {
  useCreateRole,
  useUpdateRole,
  type Permission,
  type PermissionResponse,
  type RoleResponse,
} from '@/shared/api';
import { fieldErrors } from '@/shared/lib/errors';
import { notifyError, notifySuccess } from '@/shared/lib/notify';

interface RoleFormValues {
  title: string;
  permissions: Permission[];
}

interface RoleFormModalProps {
  opened: boolean;
  onClose: () => void;
  catalog: PermissionResponse[];
  grantable: Permission[];
  role?: RoleResponse;
}

export function RoleFormModal({ opened, onClose, catalog, grantable, role }: RoleFormModalProps) {
  const form = useForm<RoleFormValues>({
    initialValues: { title: role?.title ?? '', permissions: role?.permissions ?? [] },
    validate: { title: (value) => (value.trim() ? null : 'Укажите название') },
  });
  const handlers = {
    onSuccess: () => {
      notifySuccess(role ? 'Роль сохранена' : 'Роль создана');
      onClose();
    },
    onError: (error: unknown) => {
      form.setErrors(fieldErrors(error));
      notifyError(error);
    },
  };
  const create = useCreateRole({ mutation: handlers });
  const update = useUpdateRole({ mutation: handlers });

  const submit = form.onSubmit((values) => {
    const data = { title: values.title.trim(), permissions: values.permissions };
    if (role) {
      update.mutate({ roleId: role.id, data });
    } else {
      create.mutate({ data });
    }
  });

  return (
    <Modal opened={opened} onClose={onClose} title={role ? 'Роль' : 'Новая роль'} size="lg">
      <form onSubmit={submit}>
        <Stack>
          <TextInput label="Название" withAsterisk {...form.getInputProps('title')} />
          <Checkbox.Group label="Права" {...form.getInputProps('permissions')}>
            <Stack gap="md" mt="xs">
              {groupPermissions(catalog).map(([group, permissions]) => (
                <Stack key={group} gap={6}>
                  <Text size="sm" fw={600}>
                    {PERMISSION_GROUP_TITLES[group]}
                  </Text>
                  {permissions.map((permission) => (
                    <Checkbox
                      key={permission.code}
                      value={permission.code}
                      label={permission.title}
                      disabled={!grantable.includes(permission.code)}
                    />
                  ))}
                </Stack>
              ))}
            </Stack>
          </Checkbox.Group>
          <Group justify="flex-end">
            <Button variant="default" onClick={onClose}>
              Отмена
            </Button>
            <Button type="submit" loading={create.isPending || update.isPending}>
              Сохранить
            </Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}

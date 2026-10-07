import { Button, Group, Modal, NumberInput, Select, Stack, Switch, TextInput } from '@mantine/core';
import { useForm } from '@mantine/form';

import {
  useCreateAdmin,
  useUpdateAdmin,
  type AdminUserResponse,
  type RoleResponse,
} from '@/shared/api';
import { fieldErrors } from '@/shared/lib/errors';
import { notifyError, notifySuccess } from '@/shared/lib/notify';

interface AdminFormValues {
  tg_id: number | string;
  name: string;
  role_id: string | null;
  is_active: boolean;
}

interface AdminFormModalProps {
  opened: boolean;
  onClose: () => void;
  roles: RoleResponse[];
  admin?: AdminUserResponse;
}

export function AdminFormModal({ opened, onClose, roles, admin }: AdminFormModalProps) {
  const form = useForm<AdminFormValues>({
    initialValues: {
      tg_id: admin?.tg_id ?? '',
      name: admin?.name ?? '',
      role_id: admin?.role ? String(admin.role.id) : null,
      is_active: admin?.is_active ?? true,
    },
    validate: {
      tg_id: (value) => (typeof value === 'number' && value > 0 ? null : 'Укажите Telegram id'),
      name: (value) => (value.trim() ? null : 'Укажите имя'),
      role_id: (value) => (value ? null : 'Выберите роль'),
    },
  });
  const handlers = {
    onSuccess: () => {
      notifySuccess(admin ? 'Админ сохранён' : 'Админ добавлен');
      onClose();
    },
    onError: (error: unknown) => {
      form.setErrors(fieldErrors(error));
      notifyError(error);
    },
  };
  const create = useCreateAdmin({ mutation: handlers });
  const update = useUpdateAdmin({ mutation: handlers });

  const submit = form.onSubmit((values) => {
    const roleId = Number(values.role_id);
    if (admin) {
      update.mutate({
        adminUserId: admin.id,
        data: { name: values.name.trim(), role_id: roleId, is_active: values.is_active },
      });
    } else {
      create.mutate({
        data: { tg_id: Number(values.tg_id), name: values.name.trim(), role_id: roleId },
      });
    }
  });

  return (
    <Modal opened={opened} onClose={onClose} title={admin ? 'Админ' : 'Новый админ'}>
      <form onSubmit={submit}>
        <Stack>
          <NumberInput
            label="Telegram id"
            description="Узнать id можно у @userinfobot"
            allowDecimal={false}
            allowNegative={false}
            hideControls
            disabled={Boolean(admin)}
            withAsterisk
            {...form.getInputProps('tg_id')}
          />
          <TextInput label="Имя" withAsterisk {...form.getInputProps('name')} />
          <Select
            label="Роль"
            data={roles.map((role) => ({ value: String(role.id), label: role.title }))}
            withAsterisk
            {...form.getInputProps('role_id')}
          />
          {admin && (
            <Switch
              label="Доступ включён"
              {...form.getInputProps('is_active', { type: 'checkbox' })}
            />
          )}
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

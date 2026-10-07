import { Text } from '@mantine/core';
import { modals } from '@mantine/modals';

import { useDeleteRole, type RoleResponse } from '@/shared/api';
import { notifyError, notifySuccess } from '@/shared/lib/notify';

export function useDeleteRoleConfirm(): (role: RoleResponse) => void {
  const remove = useDeleteRole({
    mutation: {
      onSuccess: () => {
        notifySuccess('Роль удалена');
      },
      onError: notifyError,
    },
  });

  return (role) => {
    modals.openConfirmModal({
      title: 'Удалить роль?',
      children: <Text size="sm">Роль «{role.title}» будет удалена.</Text>,
      labels: { confirm: 'Удалить', cancel: 'Отмена' },
      confirmProps: { color: 'red' },
      onConfirm: () => {
        remove.mutate({ roleId: role.id });
      },
    });
  };
}

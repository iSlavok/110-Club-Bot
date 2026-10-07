import { Text } from '@mantine/core';
import { modals } from '@mantine/modals';

import { useDeleteBlock, type BlockResponse } from '@/shared/api';
import { notifyError, notifySuccess } from '@/shared/lib/notify';

export function useDeleteBlockConfirm(): (block: BlockResponse) => void {
  const remove = useDeleteBlock({
    mutation: {
      onSuccess: () => {
        notifySuccess('Блок удалён');
      },
      onError: notifyError,
    },
  });

  return (block) => {
    modals.openConfirmModal({
      title: 'Удалить блок?',
      children: (
        <Text size="sm">
          Блок «{block.title}» будет удалён. Если в нём уже есть участники из таблицы, удалить не
          получится.
        </Text>
      ),
      labels: { confirm: 'Удалить', cancel: 'Отмена' },
      confirmProps: { color: 'red' },
      onConfirm: () => {
        remove.mutate({ blockId: block.id });
      },
    });
  };
}

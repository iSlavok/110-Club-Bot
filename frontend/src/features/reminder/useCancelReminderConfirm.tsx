import { Text } from '@mantine/core';
import { modals } from '@mantine/modals';

import { useCancelReminder, type ReminderResponse } from '@/shared/api';
import { formatDateTime } from '@/shared/lib/dates';
import { notifyError, notifySuccess } from '@/shared/lib/notify';

export function useCancelReminderConfirm(): (reminder: ReminderResponse) => void {
  const cancel = useCancelReminder({
    mutation: {
      onSuccess: () => {
        notifySuccess('Напоминание отменено');
      },
      onError: notifyError,
    },
  });

  return (reminder) => {
    modals.openConfirmModal({
      title: 'Отменить напоминание?',
      children: (
        <Text size="sm">
          Сообщение на {formatDateTime(reminder.send_at)} (МСК) не уйдёт в чат. Вернуть его нельзя,
          но можно заново сохранить урок с нужными напоминаниями.
        </Text>
      ),
      labels: { confirm: 'Отменить напоминание', cancel: 'Назад' },
      confirmProps: { color: 'red' },
      onConfirm: () => {
        cancel.mutate({ reminderId: reminder.id });
      },
    });
  };
}

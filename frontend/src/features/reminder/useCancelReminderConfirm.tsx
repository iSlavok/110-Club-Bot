import { Text } from '@mantine/core';
import { modals } from '@mantine/modals';

import { useCancelMessage, useCancelReminder, type ReminderResponse } from '@/shared/api';
import { formatDateTime } from '@/shared/lib/dates';
import { notifyError, notifySuccess } from '@/shared/lib/notify';

export function useCancelReminderConfirm(): (reminder: ReminderResponse) => void {
  const cancelReminder = useCancelReminder({
    mutation: {
      onSuccess: () => {
        notifySuccess('Напоминание отменено');
      },
      onError: notifyError,
    },
  });
  const cancelMessage = useCancelMessage({
    mutation: {
      onSuccess: () => {
        notifySuccess('Сообщение отменено');
      },
      onError: notifyError,
    },
  });

  return (reminder) => {
    const isMessage = reminder.kind === 'message';
    const when = formatDateTime(reminder.send_at);
    modals.openConfirmModal({
      title: isMessage ? 'Отменить сообщение?' : 'Отменить напоминание?',
      children: (
        <Text size="sm">
          {isMessage
            ? `Сообщение на ${when} не уйдёт в чат. Вернуть его нельзя, только написать заново.`
            : `Сообщение на ${when} не уйдёт в чат. Вернуть его нельзя, но можно заново сохранить урок с нужными напоминаниями.`}
        </Text>
      ),
      labels: {
        confirm: isMessage ? 'Отменить сообщение' : 'Отменить напоминание',
        cancel: 'Назад',
      },
      confirmProps: { color: 'red' },
      onConfirm: () => {
        if (isMessage) {
          cancelMessage.mutate({ messageId: reminder.id });
        } else {
          cancelReminder.mutate({ reminderId: reminder.id });
        }
      },
    });
  };
}

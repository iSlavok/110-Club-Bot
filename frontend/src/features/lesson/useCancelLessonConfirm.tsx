import { Text } from '@mantine/core';
import { modals } from '@mantine/modals';

import { useCancelLesson, type LessonResponse } from '@/shared/api';
import { notifyError, notifySuccess } from '@/shared/lib/notify';

import { askNotifyChat } from './askNotifyChat';

export function useCancelLessonConfirm(): (lesson: LessonResponse) => void {
  const cancel = useCancelLesson({
    mutation: {
      onSuccess: () => {
        notifySuccess('Урок отменён');
      },
      onError: notifyError,
    },
  });

  return (lesson) => {
    modals.openConfirmModal({
      title: 'Отменить урок?',
      children: (
        <Text size="sm">
          «{lesson.title}» будет отменён вместе с ещё не отправленными напоминаниями и ДЗ. Вернуть
          его нельзя.
        </Text>
      ),
      labels: { confirm: 'Отменить урок', cancel: 'Назад' },
      confirmProps: { color: 'red' },
      onConfirm: () => {
        void askNotifyChat(['урок отменён']).then((notify) => {
          if (notify !== null) {
            cancel.mutate({ lessonId: lesson.id, data: { notify_chat: notify } });
          }
        });
      },
    });
  };
}

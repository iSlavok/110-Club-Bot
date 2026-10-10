import { Button, Group, Stack, Text } from '@mantine/core';
import { modals } from '@mantine/modals';

import type { LessonKind } from '@/shared/api';

import type { ChatNotice } from './model';

const SUBJECT_OF: Record<LessonKind, string> = { lesson: 'урока', curator_call: 'созвона' };

function noticeTopic(notice: ChatNotice, kind: LessonKind): string {
  switch (notice) {
    case 'rescheduled':
      return `переносе ${SUBJECT_OF[kind]}`;
    case 'cancelled':
      return `отмене ${SUBJECT_OF[kind]}`;
    case 'deadline_changed':
      return 'новом дедлайне ДЗ';
    case 'homework_removed':
      return 'отмене ДЗ';
  }
}

/** «Сообщить в чат о переносе урока и отмене ДЗ?» */
export function notifyChatTitle(notices: ChatNotice[], kind: LessonKind): string {
  const topics = notices.map((notice) => noticeTopic(notice, kind)).join(' и ');
  const preposition = topics.startsWith('о') ? 'об' : 'о';
  return `Сообщить в чат ${preposition} ${topics}?`;
}

/**
 * Second window over an action that changes what the chat was told: true — send a message, false — stay
 * silent, null — the admin closed the window and the action is called off.
 */
export function askNotifyChat(notices: ChatNotice[], kind: LessonKind): Promise<boolean | null> {
  return new Promise((resolve) => {
    let answered = false;
    const answer = (value: boolean | null) => {
      if (!answered) {
        answered = true;
        resolve(value);
      }
    };
    const id = modals.open({
      title: notifyChatTitle(notices, kind),
      onClose: () => {
        answer(null);
      },
      children: (
        <Stack>
          <Text size="sm">
            Бот отправит отдельное сообщение в топик напоминаний. Запланированные напоминания
            обновятся в любом случае.
          </Text>
          <Group justify="flex-end">
            <Button
              variant="default"
              data-autofocus
              onClick={() => {
                answer(false);
                modals.close(id);
              }}
            >
              Не сообщать
            </Button>
            <Button
              onClick={() => {
                answer(true);
                modals.close(id);
              }}
            >
              Сообщить
            </Button>
          </Group>
        </Stack>
      ),
    });
  });
}

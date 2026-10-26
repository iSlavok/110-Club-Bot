import { Button, Group, Modal, SegmentedControl, Stack, Text } from '@mantine/core';
import { useState } from 'react';

import { DraftReminderPreview } from '@/entities/reminder';
import { useRemindNow, type LessonResponse, type ReminderTarget } from '@/shared/api';
import { notifyError, notifySuccess } from '@/shared/lib/notify';

import { minutesUntil } from './model';

const TARGETS: { value: ReminderTarget; label: string }[] = [
  { value: 'lesson', label: 'Об уроке' },
  { value: 'homework', label: 'О дедлайне ДЗ' },
];

interface RemindNowModalProps {
  lesson: LessonResponse;
  onClose: () => void;
}

export function RemindNowModal({ lesson, onClose }: RemindNowModalProps) {
  const hasHomework = lesson.homework_deadline_at !== null;
  const [target, setTarget] = useState<ReminderTarget>('lesson');
  const remind = useRemindNow({
    mutation: {
      onSuccess: () => {
        notifySuccess('Напоминание уйдёт в чат в течение минуты');
        onClose();
      },
      onError: notifyError,
    },
  });
  const started = minutesUntil(lesson.starts_at) < 0;
  const kind =
    target === 'homework' ? 'homework_deadline' : started ? 'lesson_starting' : 'lesson_upcoming';

  return (
    <Modal opened onClose={onClose} title="Отправить напоминание сейчас" size="lg">
      <Stack>
        {hasHomework && (
          <SegmentedControl
            aria-label="О чём напомнить"
            data={TARGETS}
            value={target}
            onChange={(value) => {
              setTarget(value);
            }}
          />
        )}
        <Text size="sm" c="dimmed">
          Сообщение уйдёт в чат клуба в начале следующей минуты. Запланированные напоминания
          останутся как есть.
        </Text>
        <DraftReminderPreview
          request={{
            lesson: {
              kind: lesson.kind,
              title: lesson.title,
              description: lesson.description,
              starts_at: lesson.starts_at,
              call_url: lesson.call_url,
              homework_deadline_at: lesson.homework_deadline_at,
            },
            kind,
          }}
        />
        <Group justify="flex-end">
          <Button variant="default" onClick={onClose}>
            Назад
          </Button>
          <Button
            loading={remind.isPending}
            onClick={() => {
              remind.mutate({ lessonId: lesson.id, data: { target } });
            }}
          >
            Отправить
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}

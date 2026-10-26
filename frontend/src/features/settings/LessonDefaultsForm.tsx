import { Button, Group, Stack, Text } from '@mantine/core';
import { TimeInput } from '@mantine/dates';
import { useForm } from '@mantine/form';

import { ReminderOffsetsInput } from '@/entities/reminder';
import { useUpdateSettings, type AppSettingsResponse } from '@/shared/api';
import { fieldErrors } from '@/shared/lib/errors';
import { notifyError, notifySuccess } from '@/shared/lib/notify';

interface LessonDefaultsFormValues {
  default_lesson_time: string;
  default_lesson_offsets: number[];
  default_homework_time: string;
  default_homework_offsets: number[];
}

interface LessonDefaultsFormProps {
  settings: AppSettingsResponse;
  canEdit: boolean;
}

const sameOffsets = (a: number[], b: number[]) =>
  a.length === b.length && a.every((value, index) => value === b[index]);

// The API sends HH:MM:SS; the time input works with HH:MM.
const toMinutes = (time: string) => time.slice(0, 5);

export function LessonDefaultsForm({ settings, canEdit }: LessonDefaultsFormProps) {
  const form = useForm<LessonDefaultsFormValues>({
    initialValues: {
      default_lesson_time: toMinutes(settings.default_lesson_time),
      default_lesson_offsets: settings.default_lesson_offsets,
      default_homework_time: toMinutes(settings.default_homework_time),
      default_homework_offsets: settings.default_homework_offsets,
    },
    validate: {
      default_lesson_time: (value) => (value ? null : 'Укажите время'),
      default_homework_time: (value) => (value ? null : 'Укажите время'),
    },
  });
  const update = useUpdateSettings({
    mutation: {
      onSuccess: () => {
        notifySuccess('Настройки сохранены');
      },
      onError: (error) => {
        form.setErrors(fieldErrors(error));
        notifyError(error);
      },
    },
  });
  const { values } = form;
  const changed = {
    lessonTime: values.default_lesson_time !== toMinutes(settings.default_lesson_time),
    lessonOffsets: !sameOffsets(values.default_lesson_offsets, settings.default_lesson_offsets),
    homeworkTime: values.default_homework_time !== toMinutes(settings.default_homework_time),
    homeworkOffsets: !sameOffsets(
      values.default_homework_offsets,
      settings.default_homework_offsets,
    ),
  };

  const submit = form.onSubmit((submitted) => {
    update.mutate({
      data: {
        ...(changed.lessonTime && { default_lesson_time: submitted.default_lesson_time }),
        ...(changed.lessonOffsets && { default_lesson_offsets: submitted.default_lesson_offsets }),
        ...(changed.homeworkTime && { default_homework_time: submitted.default_homework_time }),
        ...(changed.homeworkOffsets && {
          default_homework_offsets: submitted.default_homework_offsets,
        }),
      },
    });
  });

  return (
    <form onSubmit={submit} aria-label="Новый урок по умолчанию">
      <Stack>
        <div>
          <Text fw={600}>Новый урок по умолчанию</Text>
          <Text size="sm" c="dimmed">
            Подставляется в форму нового урока. На созданные уроки не влияет.
          </Text>
        </div>
        <TimeInput
          label="Время начала урока"
          disabled={!canEdit}
          w={160}
          {...form.getInputProps('default_lesson_time')}
        />
        <ReminderOffsetsInput
          label="Напоминания об уроке"
          disabled={!canEdit}
          value={values.default_lesson_offsets}
          onChange={(value) => {
            form.setFieldValue('default_lesson_offsets', value);
          }}
          error={form.errors.default_lesson_offsets}
        />
        <TimeInput
          label="Время дедлайна ДЗ"
          disabled={!canEdit}
          w={160}
          {...form.getInputProps('default_homework_time')}
        />
        <ReminderOffsetsInput
          label="Напоминания о дедлайне ДЗ"
          zeroLabel="в момент дедлайна"
          disabled={!canEdit}
          value={values.default_homework_offsets}
          onChange={(value) => {
            form.setFieldValue('default_homework_offsets', value);
          }}
          error={form.errors.default_homework_offsets}
        />
        {canEdit && (
          <Group>
            <Button
              type="submit"
              loading={update.isPending}
              disabled={!Object.values(changed).some(Boolean)}
            >
              Сохранить
            </Button>
          </Group>
        )}
      </Stack>
    </form>
  );
}

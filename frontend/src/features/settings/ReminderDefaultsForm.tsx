import { Button, Group, Stack, Text } from '@mantine/core';
import { useForm } from '@mantine/form';

import { ReminderOffsetsInput } from '@/entities/reminder';
import { useUpdateSettings, type AppSettingsResponse } from '@/shared/api';
import { fieldErrors } from '@/shared/lib/errors';
import { notifyError, notifySuccess } from '@/shared/lib/notify';

interface ReminderDefaultsFormValues {
  default_lesson_offsets: number[];
  default_homework_offsets: number[];
}

interface ReminderDefaultsFormProps {
  settings: AppSettingsResponse;
  canEdit: boolean;
}

const sameOffsets = (a: number[], b: number[]) =>
  a.length === b.length && a.every((value, index) => value === b[index]);

export function ReminderDefaultsForm({ settings, canEdit }: ReminderDefaultsFormProps) {
  const form = useForm<ReminderDefaultsFormValues>({
    initialValues: {
      default_lesson_offsets: settings.default_lesson_offsets,
      default_homework_offsets: settings.default_homework_offsets,
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
  const changed = {
    lesson: !sameOffsets(form.values.default_lesson_offsets, settings.default_lesson_offsets),
    homework: !sameOffsets(form.values.default_homework_offsets, settings.default_homework_offsets),
  };

  const submit = form.onSubmit((values) => {
    update.mutate({
      data: {
        ...(changed.lesson && { default_lesson_offsets: values.default_lesson_offsets }),
        ...(changed.homework && { default_homework_offsets: values.default_homework_offsets }),
      },
    });
  });

  return (
    <form onSubmit={submit} aria-label="Напоминания по умолчанию">
      <Stack>
        <div>
          <Text fw={600}>Напоминания по умолчанию</Text>
          <Text size="sm" c="dimmed">
            Подставляются в форму нового урока, там их можно поменять. На уже созданные уроки не
            влияют.
          </Text>
        </div>
        <ReminderOffsetsInput
          label="Об уроке"
          description="За сколько до начала напомнить в топике чата"
          disabled={!canEdit}
          value={form.values.default_lesson_offsets}
          onChange={(value) => {
            form.setFieldValue('default_lesson_offsets', value);
          }}
          error={form.errors.default_lesson_offsets}
        />
        <ReminderOffsetsInput
          label="О дедлайне ДЗ"
          description="За сколько до дедлайна напомнить в топике чата"
          zeroLabel="в момент дедлайна"
          disabled={!canEdit}
          value={form.values.default_homework_offsets}
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
              disabled={!changed.lesson && !changed.homework}
            >
              Сохранить
            </Button>
          </Group>
        )}
      </Stack>
    </form>
  );
}

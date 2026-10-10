import {
  Alert,
  Button,
  Checkbox,
  Group,
  Modal,
  SegmentedControl,
  Stack,
  Switch,
  Textarea,
  TextInput,
} from '@mantine/core';
import { DateTimePicker } from '@mantine/dates';
import { useForm } from '@mantine/form';

import { LESSON_KIND_LABELS } from '@/entities/lesson';
import {
  formatOffset,
  latestFirst,
  MAX_OFFSET_MINUTES,
  ReminderOffsetsInput,
} from '@/entities/reminder';
import {
  useCreateLesson,
  useGetSettings,
  useUpdateLesson,
  type LessonKind,
  type LessonResponse,
} from '@/shared/api';
import { fromPickerValue, toPickerValue } from '@/shared/lib/dates';
import { fieldErrors } from '@/shared/lib/errors';
import { notifyError, notifySuccess } from '@/shared/lib/notify';

import { askNotifyChat } from './askNotifyChat';
import { chatNotices, homeworkRemindersBeforeStart, minutesUntil } from './model';

interface LessonFormValues {
  kind: LessonKind;
  title: string;
  starts_at: string | null;
  call_url: string;
  description: string;
  reminder_offsets: number[];
  remind_now: boolean;
  has_homework: boolean;
  homework_deadline_at: string | null;
  homework_reminder_offsets: number[];
}

interface LessonFormModalProps {
  onClose: () => void;
  clubId: number;
  lesson?: LessonResponse;
}

const KINDS: { value: LessonKind; label: string }[] = [
  { value: 'lesson', label: LESSON_KIND_LABELS.lesson },
  { value: 'curator_call', label: LESSON_KIND_LABELS.curator_call },
];

export function LessonFormModal({ onClose, clubId, lesson }: LessonFormModalProps) {
  const settings = useGetSettings({ query: { enabled: !lesson } });
  return (
    <Modal opened onClose={onClose} title={lesson ? 'Урок' : 'Новый урок'} size="lg">
      {lesson || settings.data ? (
        <LessonForm
          onClose={onClose}
          clubId={clubId}
          lesson={lesson}
          defaults={{
            reminder_offsets:
              lesson?.reminder_offsets ?? settings.data?.default_lesson_offsets ?? [],
            homework_reminder_offsets:
              lesson?.homework_reminder_offsets ?? settings.data?.default_homework_offsets ?? [],
          }}
        />
      ) : (
        <Alert color={settings.error ? 'red' : 'gray'}>
          {settings.error ? 'Не удалось загрузить настройки напоминаний' : 'Загрузка…'}
        </Alert>
      )}
    </Modal>
  );
}

interface LessonFormProps extends LessonFormModalProps {
  defaults: { reminder_offsets: number[]; homework_reminder_offsets: number[] };
}

function LessonForm({ onClose, clubId, lesson, defaults }: LessonFormProps) {
  const form = useForm<LessonFormValues>({
    initialValues: {
      kind: lesson?.kind ?? 'lesson',
      title: lesson?.title ?? '',
      starts_at: lesson ? toPickerValue(lesson.starts_at) : null,
      call_url: lesson?.call_url ?? '',
      description: lesson?.description ?? '',
      reminder_offsets: defaults.reminder_offsets,
      remind_now: false,
      has_homework: Boolean(lesson?.homework_deadline_at),
      homework_deadline_at: lesson?.homework_deadline_at
        ? toPickerValue(lesson.homework_deadline_at)
        : null,
      homework_reminder_offsets: defaults.homework_reminder_offsets,
    },
    validate: {
      title: (value) => (value.trim() ? null : 'Укажите тему'),
      starts_at: (value) => (value ? null : 'Укажите начало'),
      call_url: (value) =>
        !value.trim() || /^https?:\/\/[^\s<>"']+$/.test(value.trim())
          ? null
          : 'Ссылка вида https://…',
      homework_deadline_at: (value, values) =>
        values.has_homework && !value ? 'Укажите дедлайн' : null,
    },
  });
  const handlers = {
    onSuccess: () => {
      notifySuccess(lesson ? 'Урок сохранён' : 'Урок создан');
      onClose();
    },
    onError: (error: unknown) => {
      form.setErrors(fieldErrors(error));
      notifyError(error);
    },
  };
  const create = useCreateLesson({ mutation: handlers });
  const update = useUpdateLesson({ mutation: handlers });

  const { values } = form;
  const earlyHomework =
    values.has_homework && values.starts_at && values.homework_deadline_at
      ? homeworkRemindersBeforeStart(
          fromPickerValue(values.starts_at),
          fromPickerValue(values.homework_deadline_at),
          values.homework_reminder_offsets,
        )
      : [];

  const submit = form.onSubmit(async (submitted) => {
    if (!submitted.starts_at) {
      return;
    }
    const startsAt = fromPickerValue(submitted.starts_at);
    let reminderOffsets = submitted.reminder_offsets;
    if (submitted.remind_now) {
      const minutes = minutesUntil(startsAt);
      if (minutes < 0 || minutes > MAX_OFFSET_MINUTES) {
        form.setFieldError(
          'remind_now',
          minutes < 0 ? 'Урок уже начался' : 'До урока больше 30 дней',
        );
        return;
      }
      reminderOffsets = latestFirst([...reminderOffsets, minutes]);
    }
    const homeworkDeadline =
      submitted.has_homework && submitted.homework_deadline_at
        ? fromPickerValue(submitted.homework_deadline_at)
        : null;
    const data = {
      kind: submitted.kind,
      title: submitted.title.trim(),
      starts_at: startsAt,
      call_url: submitted.call_url.trim() || null,
      description: submitted.description.trim() || null,
      reminder_offsets: reminderOffsets,
      homework_deadline_at: homeworkDeadline,
      homework_reminder_offsets: submitted.homework_reminder_offsets,
    };
    if (!lesson) {
      create.mutate({ clubId, data });
      return;
    }
    const notices = chatNotices(lesson, {
      starts_at: startsAt,
      homework_deadline_at: homeworkDeadline,
    });
    const notify = notices.length > 0 ? await askNotifyChat(notices) : false;
    if (notify !== null) {
      update.mutate({
        lessonId: lesson.id,
        data,
        params: notify ? { notify_chat: true } : undefined,
      });
    }
  });

  return (
    <form onSubmit={submit}>
      <Stack>
        <SegmentedControl
          aria-label="Тип"
          data={KINDS}
          value={values.kind}
          onChange={(value) => {
            form.setFieldValue('kind', value);
          }}
        />
        <TextInput label="Тема" withAsterisk {...form.getInputProps('title')} />
        <DateTimePicker
          label="Начало (МСК)"
          valueFormat="DD.MM.YYYY HH:mm"
          withAsterisk
          {...form.getInputProps('starts_at')}
        />
        <TextInput
          label="Ссылка на созвон"
          placeholder="https://…"
          {...form.getInputProps('call_url')}
        />
        <Textarea
          label="Описание"
          description="Попадёт в напоминание об уроке"
          autosize
          minRows={2}
          maxRows={6}
          {...form.getInputProps('description')}
        />
        <ReminderOffsetsInput
          label="Напоминания об уроке"
          description="За сколько до начала напомнить в топике чата"
          value={values.reminder_offsets}
          onChange={(value) => {
            form.setFieldValue('reminder_offsets', value);
          }}
          error={form.errors.reminder_offsets}
        />
        <Checkbox
          label="Ещё напомнить сейчас — сразу после сохранения"
          {...form.getInputProps('remind_now', { type: 'checkbox' })}
        />
        <Switch label="Есть ДЗ" {...form.getInputProps('has_homework', { type: 'checkbox' })} />
        {values.has_homework && (
          <>
            <DateTimePicker
              label="Дедлайн ДЗ (МСК)"
              valueFormat="DD.MM.YYYY HH:mm"
              withAsterisk
              {...form.getInputProps('homework_deadline_at')}
            />
            <ReminderOffsetsInput
              label="Напоминания о дедлайне"
              description="За сколько до дедлайна напомнить в топике чата"
              zeroLabel="в момент дедлайна"
              value={values.homework_reminder_offsets}
              onChange={(value) => {
                form.setFieldValue('homework_reminder_offsets', value);
              }}
              error={form.errors.homework_reminder_offsets}
            />
            {earlyHomework.length > 0 && (
              <Alert color="yellow" title="Напоминание о ДЗ раньше урока">
                {earlyHomework
                  .map((offset) => formatOffset(offset, 'в момент дедлайна'))
                  .join(', ')}{' '}
                — уйдёт в чат ещё до начала урока. Сохранить так можно.
              </Alert>
            )}
          </>
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
  );
}

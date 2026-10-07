import { Button, Group, Modal, NumberInput, Stack, Switch, TextInput } from '@mantine/core';
import { useForm } from '@mantine/form';

import { useCreateClub, useUpdateClub, type ClubCreate, type ClubResponse } from '@/shared/api';
import { fieldErrors } from '@/shared/lib/errors';
import { notifyError, notifySuccess } from '@/shared/lib/notify';

interface ClubFormValues {
  title: string;
  chat_id: number | string;
  reminders_topic_id: number | string;
  spreadsheet_id: string;
  sheet_name: string;
  is_active: boolean;
}

interface ClubFormModalProps {
  opened: boolean;
  onClose: () => void;
  club?: ClubResponse;
}

function toValues(club?: ClubResponse): ClubFormValues {
  return {
    title: club?.title ?? '',
    chat_id: club?.chat_id ?? '',
    reminders_topic_id: club?.reminders_topic_id ?? '',
    spreadsheet_id: club?.spreadsheet_id ?? '',
    sheet_name: club?.sheet_name ?? '',
    is_active: club?.is_active ?? true,
  };
}

function toBody(values: ClubFormValues): ClubCreate {
  return {
    title: values.title.trim(),
    chat_id: typeof values.chat_id === 'number' ? values.chat_id : null,
    reminders_topic_id:
      typeof values.reminders_topic_id === 'number' ? values.reminders_topic_id : null,
    spreadsheet_id: values.spreadsheet_id.trim() || null,
    sheet_name: values.sheet_name.trim() || null,
  };
}

export function ClubFormModal({ opened, onClose, club }: ClubFormModalProps) {
  const form = useForm<ClubFormValues>({
    initialValues: toValues(club),
    validate: { title: (value) => (value.trim() ? null : 'Укажите название') },
  });
  const handlers = {
    onSuccess: () => {
      notifySuccess(club ? 'Клуб сохранён' : 'Клуб создан');
      onClose();
    },
    onError: (error: unknown) => {
      form.setErrors(fieldErrors(error));
      notifyError(error);
    },
  };
  const create = useCreateClub({ mutation: handlers });
  const update = useUpdateClub({ mutation: handlers });

  const submit = form.onSubmit((values) => {
    const body = toBody(values);
    if (club) {
      update.mutate({ clubId: club.id, data: { ...body, is_active: values.is_active } });
    } else {
      create.mutate({ data: body });
    }
  });

  return (
    <Modal opened={opened} onClose={onClose} title={club ? 'Клуб' : 'Новый клуб'} size="lg">
      <form onSubmit={submit}>
        <Stack>
          <TextInput label="Название" withAsterisk {...form.getInputProps('title')} />
          <Group grow align="flex-start">
            <NumberInput
              label="ID чата"
              description="Отрицательное число, например -100…"
              allowDecimal={false}
              hideControls
              {...form.getInputProps('chat_id')}
            />
            <NumberInput
              label="ID топика напоминаний"
              allowDecimal={false}
              allowNegative={false}
              hideControls
              {...form.getInputProps('reminders_topic_id')}
            />
          </Group>
          <TextInput
            label="ID Google-таблицы"
            description="Часть ссылки между /d/ и /edit"
            {...form.getInputProps('spreadsheet_id')}
          />
          <TextInput label="Лист с составом" {...form.getInputProps('sheet_name')} />
          {club && (
            <Switch
              label="Клуб активен"
              {...form.getInputProps('is_active', { type: 'checkbox' })}
            />
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
    </Modal>
  );
}

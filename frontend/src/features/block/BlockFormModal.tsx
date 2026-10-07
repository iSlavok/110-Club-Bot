import { Button, Group, Modal, Stack, TextInput } from '@mantine/core';
import { DateTimePicker } from '@mantine/dates';
import { useForm } from '@mantine/form';

import { useCreateBlock, useUpdateBlock, type BlockResponse } from '@/shared/api';
import { fromPickerValue, toPickerValue } from '@/shared/lib/dates';
import { fieldErrors } from '@/shared/lib/errors';
import { notifyError, notifySuccess } from '@/shared/lib/notify';

interface BlockFormValues {
  title: string;
  sheet_column_title: string;
  starts_at: string | null;
  ends_at: string | null;
}

interface BlockFormModalProps {
  opened: boolean;
  onClose: () => void;
  clubId: number;
  block?: BlockResponse;
}

const required = (message: string) => (value: string | null) => (value?.trim() ? null : message);

export function BlockFormModal({ opened, onClose, clubId, block }: BlockFormModalProps) {
  const form = useForm<BlockFormValues>({
    initialValues: {
      title: block?.title ?? '',
      sheet_column_title: block?.sheet_column_title ?? '',
      starts_at: block ? toPickerValue(block.starts_at) : null,
      ends_at: block ? toPickerValue(block.ends_at) : null,
    },
    validate: {
      title: required('Укажите название'),
      sheet_column_title: required('Укажите заголовок столбца'),
      starts_at: required('Укажите начало'),
      ends_at: (value, values) => {
        if (!value) {
          return 'Укажите конец';
        }
        return values.starts_at && value <= values.starts_at
          ? 'Конец должен быть позже начала'
          : null;
      },
    },
  });
  const handlers = {
    onSuccess: () => {
      notifySuccess(block ? 'Блок сохранён' : 'Блок создан');
      onClose();
    },
    onError: (error: unknown) => {
      form.setErrors(fieldErrors(error));
      notifyError(error);
    },
  };
  const create = useCreateBlock({ mutation: handlers });
  const update = useUpdateBlock({ mutation: handlers });

  const submit = form.onSubmit((values) => {
    if (!values.starts_at || !values.ends_at) {
      return;
    }
    const data = {
      title: values.title.trim(),
      sheet_column_title: values.sheet_column_title.trim(),
      starts_at: fromPickerValue(values.starts_at),
      ends_at: fromPickerValue(values.ends_at),
    };
    if (block) {
      update.mutate({ blockId: block.id, data });
    } else {
      create.mutate({ clubId, data });
    }
  });

  return (
    <Modal opened={opened} onClose={onClose} title={block ? 'Блок' : 'Новый блок'} size="lg">
      <form onSubmit={submit}>
        <Stack>
          <TextInput label="Название" withAsterisk {...form.getInputProps('title')} />
          <TextInput
            label="Заголовок столбца в таблице"
            description="Должен совпадать со строкой 2 листа, например «Блок 5»"
            withAsterisk
            {...form.getInputProps('sheet_column_title')}
          />
          <Group grow align="flex-start">
            <DateTimePicker
              label="Начало (МСК)"
              valueFormat="DD.MM.YYYY HH:mm"
              withAsterisk
              {...form.getInputProps('starts_at')}
            />
            <DateTimePicker
              label="Конец (МСК)"
              valueFormat="DD.MM.YYYY HH:mm"
              withAsterisk
              {...form.getInputProps('ends_at')}
            />
          </Group>
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

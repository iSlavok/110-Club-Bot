import {
  Button,
  Group,
  Loader,
  Modal,
  SegmentedControl,
  SimpleGrid,
  Stack,
  Text,
} from '@mantine/core';
import { DateTimePicker } from '@mantine/dates';
import { useForm } from '@mantine/form';
import { lazy, Suspense } from 'react';

import { ReminderMessage } from '@/entities/reminder';
import { useCreateMessage, useUpdateMessage, type ReminderResponse } from '@/shared/api';
import { formatDateTime, fromPickerValue, toPickerValue } from '@/shared/lib/dates';
import { fieldErrors } from '@/shared/lib/errors';
import { notifyError, notifySuccess } from '@/shared/lib/notify';
import { TELEGRAM_TEXT_MAX_LEN, telegramTextLength } from '@/shared/lib/telegram-html';

// The editor is most of the admin bundle by weight and only this form needs it.
const TelegramEditor = lazy(async () => {
  const module = await import('@/shared/ui/TelegramEditor');
  return { default: module.TelegramEditor };
});

type When = 'now' | 'later';

interface MessageFormValues {
  text: string;
  when: When;
  send_at: string | null;
}

interface MessageFormModalProps {
  clubId: number;
  /** A pending message to change; without it a new one is written. */
  message?: ReminderResponse;
  onClose: () => void;
}

export function MessageFormModal({ clubId, message, onClose }: MessageFormModalProps) {
  const form = useForm<MessageFormValues>({
    initialValues: {
      text: message?.text ?? '',
      when: message ? 'later' : 'now',
      send_at: message ? toPickerValue(message.send_at) : null,
    },
    validate: {
      text: (value) => {
        const length = telegramTextLength(value);
        if (!value.trim() || length === 0) {
          return 'Напишите сообщение';
        }
        return length > TELEGRAM_TEXT_MAX_LEN
          ? `Telegram принимает до ${String(TELEGRAM_TEXT_MAX_LEN)} символов, сейчас ${String(length)}`
          : null;
      },
      send_at: (value, values) => (values.when === 'later' && !value ? 'Укажите время' : null),
    },
  });
  const onError = (error: unknown) => {
    form.setErrors(fieldErrors(error));
    notifyError(error);
  };
  const onSaved = (saved: ReminderResponse) => {
    notifySuccess(
      form.values.when === 'now'
        ? 'Сообщение уйдёт в чат в течение минуты'
        : `Сообщение уйдёт ${formatDateTime(saved.send_at)}`,
    );
    onClose();
  };
  const create = useCreateMessage({ mutation: { onSuccess: onSaved, onError } });
  const update = useUpdateMessage({ mutation: { onSuccess: onSaved, onError } });
  const { values } = form;

  const submit = form.onSubmit((submitted) => {
    const sendAt =
      submitted.when === 'later' && submitted.send_at ? fromPickerValue(submitted.send_at) : null;
    if (message) {
      update.mutate({
        messageId: message.id,
        data: {
          ...(submitted.text !== message.text && { text: submitted.text }),
          ...((submitted.when === 'now' ||
            submitted.send_at !== toPickerValue(message.send_at)) && {
            send_at: sendAt,
          }),
        },
      });
    } else {
      create.mutate({ clubId, data: { text: submitted.text, send_at: sendAt } });
    }
  });

  return (
    <Modal
      opened
      onClose={onClose}
      title={message ? 'Изменить сообщение' : 'Сообщение в чат'}
      size="xl"
    >
      <form onSubmit={submit} aria-label="Сообщение в чат">
        <Stack>
          <SimpleGrid cols={{ base: 1, md: 2 }}>
            <Suspense fallback={<Loader size="sm" />}>
              <TelegramEditor
                label="Текст"
                initialValue={message?.text ?? ''}
                onChange={(html) => {
                  form.setFieldValue('text', html);
                }}
                error={form.errors.text}
              />
            </Suspense>
            <Stack gap={4}>
              <Text size="sm" fw={500}>
                Так увидят в чате
              </Text>
              {values.text ? (
                <ReminderMessage html={values.text} />
              ) : (
                <Text size="sm" c="dimmed">
                  Здесь появится сообщение.
                </Text>
              )}
            </Stack>
          </SimpleGrid>
          <SegmentedControl
            aria-label="Когда отправить"
            w="fit-content"
            data={[
              { value: 'now', label: 'Сейчас' },
              { value: 'later', label: 'Запланировать' },
            ]}
            {...form.getInputProps('when')}
          />
          {values.when === 'later' && (
            <DateTimePicker
              label="Когда"
              valueFormat="DD.MM.YYYY HH:mm"
              minDate={new Date()}
              withAsterisk
              w={240}
              {...form.getInputProps('send_at')}
            />
          )}
          <Text size="sm" c="dimmed">
            Сообщение уйдёт в топик напоминаний клуба. До отправки его можно изменить или отменить.
          </Text>
          <Group justify="flex-end">
            <Button variant="default" onClick={onClose}>
              Назад
            </Button>
            <Button type="submit" loading={create.isPending || update.isPending}>
              {values.when === 'now' ? 'Отправить' : 'Запланировать'}
            </Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  );
}

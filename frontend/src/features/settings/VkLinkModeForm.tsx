import { Button, Group, Radio, Stack, Text } from '@mantine/core';
import { useForm } from '@mantine/form';

import { useUpdateSettings, type AppSettingsResponse, type VkLinkMode } from '@/shared/api';
import { notifyError, notifySuccess } from '@/shared/lib/notify';

interface ModeOption {
  value: VkLinkMode;
  label: string;
  description: string;
  missing: string;
}

const MODES: ModeOption[] = [
  {
    value: 'oauth',
    label: 'Вход через VK ID',
    description:
      'Ученик нажимает кнопку в боте и входит в VK — так подтверждается, что страница его. Основной режим.',
    missing: 'Не настроено на сервере: нужны VK_CLIENT_ID и PUBLIC_URL.',
  },
  {
    value: 'link',
    label: 'Ссылка на страницу',
    description:
      'Ученик присылает ссылку на свою страницу VK и подтверждает имя. Владение страницей не проверяется.',
    missing: 'Не настроено на сервере: нужен VK_SERVICE_TOKEN.',
  },
];

interface VkLinkModeFormValues {
  vk_link_mode: VkLinkMode;
}

interface VkLinkModeFormProps {
  settings: AppSettingsResponse;
  canEdit: boolean;
}

export function VkLinkModeForm({ settings, canEdit }: VkLinkModeFormProps) {
  const form = useForm<VkLinkModeFormValues>({
    initialValues: { vk_link_mode: settings.vk_link_mode },
  });
  const update = useUpdateSettings({
    mutation: {
      onSuccess: () => {
        notifySuccess('Настройки сохранены');
      },
      onError: notifyError,
    },
  });

  const submit = form.onSubmit((values) => {
    update.mutate({ data: values });
  });

  return (
    <form onSubmit={submit}>
      <Stack>
        <Radio.Group
          label="Привязка VK в боте"
          description="Привязка окончательная: сменить или отвязать VK ученик не может ни в каком режиме."
          {...form.getInputProps('vk_link_mode')}
        >
          <Stack mt="sm" gap="sm">
            {MODES.map((option) => {
              const configured = settings.configured_vk_link_modes.includes(option.value);
              return (
                <Radio.Card
                  key={option.value}
                  value={option.value}
                  disabled={!canEdit || !configured}
                  aria-label={option.label}
                  p="md"
                  radius="md"
                >
                  <Group wrap="nowrap" align="flex-start">
                    <Radio.Indicator />
                    <div>
                      <Text fw={600}>{option.label}</Text>
                      <Text size="sm" c="dimmed">
                        {option.description}
                      </Text>
                      {!configured && (
                        <Text size="sm" c="orange">
                          {option.missing}
                        </Text>
                      )}
                    </div>
                  </Group>
                </Radio.Card>
              );
            })}
          </Stack>
        </Radio.Group>
        {canEdit && (
          <Group>
            <Button
              type="submit"
              loading={update.isPending}
              disabled={form.values.vk_link_mode === settings.vk_link_mode}
            >
              Сохранить
            </Button>
          </Group>
        )}
      </Stack>
    </form>
  );
}

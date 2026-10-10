import { Button, Group, Stack, Text } from '@mantine/core';
import { modals } from '@mantine/modals';

/**
 * Second window over an action that changes what the chat was told: true — send a message, false — stay
 * silent, null — the admin closed the window and the action is called off.
 */
export function askNotifyChat(changes: string[]): Promise<boolean | null> {
  return new Promise((resolve) => {
    let answered = false;
    const answer = (value: boolean | null) => {
      if (!answered) {
        answered = true;
        resolve(value);
      }
    };
    const id = modals.open({
      title: 'Сообщить в чат?',
      onClose: () => {
        answer(null);
      },
      children: (
        <Stack>
          <Text size="sm">
            В топик чата уйдёт сообщение: {changes.join(', ')}. Обычные напоминания бот
            перепланирует сам в любом случае.
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
              Нет
            </Button>
            <Button
              onClick={() => {
                answer(true);
                modals.close(id);
              }}
            >
              Да, сообщить
            </Button>
          </Group>
        </Stack>
      ),
    });
  });
}

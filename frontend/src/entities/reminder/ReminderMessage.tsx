import { Button, Group, Stack } from '@mantine/core';

import type { ReminderButtonResponse } from '@/shared/api';
import classes from '@/shared/ui/telegram.module.css';

interface ReminderMessageProps {
  html: string;
  buttons?: ReminderButtonResponse[];
}

export function ReminderMessage({ html, buttons = [] }: ReminderMessageProps) {
  return (
    <div className={classes.chat}>
      <Stack gap={4} className={classes.bubble}>
        {/* Safe to inject: the backend escapes admin-entered text and allows only Telegram tags; a draft is
            written by editorToTelegram, which does the same. */}
        <div
          data-testid="reminder-preview"
          className={`${classes.message} ${classes.text}`}
          style={{ whiteSpace: 'pre-wrap' }}
          dangerouslySetInnerHTML={{ __html: html }}
        />
        {buttons.length > 0 && (
          <Group gap={4} grow>
            {buttons.map((button) => (
              <Button
                key={button.url}
                component="a"
                href={button.url}
                target="_blank"
                rel="noreferrer"
                variant="default"
                radius="md"
                size="sm"
              >
                {button.text}
              </Button>
            ))}
          </Group>
        )}
      </Stack>
    </div>
  );
}

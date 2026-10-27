import { Paper } from '@mantine/core';

import classes from '@/shared/ui/telegram.module.css';

export function ReminderMessage({ html }: { html: string }) {
  return (
    <Paper withBorder p="md" radius="md" bg="var(--mantine-color-default-hover)">
      {/* Safe to inject: the backend escapes admin-entered text and allows only Telegram tags; a draft is
          written by editorToTelegram, which does the same. */}
      <div
        data-testid="reminder-preview"
        className={classes.message}
        style={{ whiteSpace: 'pre-wrap' }}
        dangerouslySetInnerHTML={{ __html: html }}
      />
    </Paper>
  );
}

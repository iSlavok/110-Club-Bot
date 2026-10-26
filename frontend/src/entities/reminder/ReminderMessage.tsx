import { Paper } from '@mantine/core';

export function ReminderMessage({ html }: { html: string }) {
  return (
    <Paper withBorder p="md" radius="md" bg="var(--mantine-color-default-hover)">
      {/* Safe to inject: the backend escapes every admin-entered field, the only tags are its own. */}
      <div
        data-testid="reminder-preview"
        style={{ whiteSpace: 'pre-wrap' }}
        dangerouslySetInnerHTML={{ __html: html }}
      />
    </Paper>
  );
}

import { Anchor } from '@mantine/core';

// One line in a table cell: a long username is cut with an ellipsis and shown whole on hover.
export function TelegramLink({ username }: { username: string }) {
  return (
    <Anchor
      href={`https://t.me/${username}`}
      target="_blank"
      rel="noreferrer"
      display="block"
      truncate="end"
      title={`@${username}`}
    >
      @{username}
    </Anchor>
  );
}

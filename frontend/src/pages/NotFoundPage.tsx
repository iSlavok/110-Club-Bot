import { Button, Center, Stack, Text, Title } from '@mantine/core';
import { Link } from 'react-router';

import { routes } from '@/shared/config/routes';

export function NotFoundPage() {
  return (
    <Center mih="60vh">
      <Stack align="center">
        <Title order={2}>Страница не найдена</Title>
        <Text c="dimmed">Возможно, ссылка устарела.</Text>
        <Button component={Link} to={routes.home} variant="default">
          На главную
        </Button>
      </Stack>
    </Center>
  );
}

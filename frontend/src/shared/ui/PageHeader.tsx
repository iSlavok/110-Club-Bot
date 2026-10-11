import { Group, Title } from '@mantine/core';
import type { ReactNode } from 'react';

interface PageHeaderProps {
  title: ReactNode;
  actions?: ReactNode;
}

export function PageHeader({ title, actions }: PageHeaderProps) {
  return (
    <Group justify="space-between" mb="lg" wrap="wrap">
      <Title order={2}>{title}</Title>
      {actions}
    </Group>
  );
}

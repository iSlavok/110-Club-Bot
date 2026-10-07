import { Paper, SimpleGrid, Text } from '@mantine/core';

import { useGetDashboardStats, type DashboardStatsResponse } from '@/shared/api';
import { PageHeader } from '@/shared/ui/PageHeader';
import { QueryState } from '@/shared/ui/QueryState';

const CARDS: { key: keyof DashboardStatsResponse; label: string }[] = [
  { key: 'active_clubs', label: 'Активных клубов' },
  { key: 'current_blocks', label: 'Блоков идёт сейчас' },
  { key: 'users', label: 'Пользователей бота' },
  { key: 'users_with_vk', label: 'С привязанным VK' },
];

export function DashboardPage() {
  const stats = useGetDashboardStats();
  return (
    <>
      <PageHeader title="Обзор" />
      <QueryState data={stats.data} error={stats.error} isPending={stats.isPending}>
        {(data) => (
          <SimpleGrid cols={{ base: 1, xs: 2, md: 4 }}>
            {CARDS.map(({ key, label }) => (
              <Paper key={key} withBorder radius="md" p="md">
                <Text size="xs" c="dimmed" tt="uppercase" fw={600}>
                  {label}
                </Text>
                <Text fz={32} fw={700}>
                  {data[key]}
                </Text>
              </Paper>
            ))}
          </SimpleGrid>
        )}
      </QueryState>
    </>
  );
}

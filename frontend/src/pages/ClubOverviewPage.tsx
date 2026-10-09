import { Group, Paper, SimpleGrid, Stack, Text } from '@mantine/core';
import type { ReactNode } from 'react';

import { BlockStatusBadge } from '@/entities/block';
import { useGetClubStats } from '@/shared/api';
import { useClubId } from '@/shared/lib/club-id';
import { formatDateTime } from '@/shared/lib/dates';
import { PageHeader } from '@/shared/ui/PageHeader';
import { QueryState } from '@/shared/ui/QueryState';

function StatCard({ label, children }: { label: string; children: ReactNode }) {
  return (
    <Paper withBorder radius="md" p="md">
      <Text size="xs" c="dimmed" tt="uppercase" fw={600} mb={4}>
        {label}
      </Text>
      {children}
    </Paper>
  );
}

export function ClubOverviewPage() {
  const stats = useGetClubStats(useClubId());
  return (
    <>
      <PageHeader title="Обзор" />
      <QueryState data={stats.data} error={stats.error} isPending={stats.isPending}>
        {({ current_block: current }) =>
          current ? (
            <SimpleGrid cols={{ base: 1, sm: 3 }}>
              <StatCard label="Текущий блок">
                <Stack gap={4}>
                  <Group gap="xs">
                    <Text fz="xl" fw={700}>
                      {current.block.title}
                    </Text>
                    <BlockStatusBadge block={current.block} />
                  </Group>
                  <Text size="sm" c="dimmed">
                    {formatDateTime(current.block.starts_at)} —{' '}
                    {formatDateTime(current.block.ends_at)}
                  </Text>
                </Stack>
              </StatCard>
              <StatCard label="Участников в блоке">
                <Text fz={32} fw={700}>
                  {current.members}
                </Text>
              </StatCard>
              <StatCard label="Из них в боте">
                <Text fz={32} fw={700}>
                  {current.members_with_tg}
                </Text>
              </StatCard>
            </SimpleGrid>
          ) : (
            <StatCard label="Текущий блок">
              <Text c="dimmed">Сейчас блока нет</Text>
            </StatCard>
          )
        }
      </QueryState>
    </>
  );
}

import { Anchor, Group, Paper, SimpleGrid, Stack, Text } from '@mantine/core';
import type { ReactNode } from 'react';
import { Link } from 'react-router';

import { BlockStatusBadge } from '@/entities/block';
import { SyncStatusBadge } from '@/entities/sheet-sync';
import { useGetClubStats, type ClubStatsResponse, type SheetSyncResponse } from '@/shared/api';
import { routes } from '@/shared/config/routes';
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

function CurrentBlock({ current }: { current: ClubStatsResponse['current_block'] }) {
  if (!current) {
    return (
      <StatCard label="Текущий блок">
        <Text c="dimmed">Сейчас блока нет</Text>
      </StatCard>
    );
  }
  return (
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
            {formatDateTime(current.block.starts_at)} — {formatDateTime(current.block.ends_at)}
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
  );
}

function LastSync({ clubId, sync }: { clubId: number; sync: SheetSyncResponse | null }) {
  return (
    <StatCard label="Синк таблицы">
      {sync ? (
        <Group gap="md">
          <SyncStatusBadge status={sync.status} />
          <Text size="sm">{formatDateTime(sync.finished_at)}</Text>
          {sync.issues.length > 0 && (
            <Text size="sm" c="orange.7">
              Проблем в таблице: {sync.issues.length}
            </Text>
          )}
          <Anchor component={Link} to={routes.clubSync(clubId)} size="sm">
            Подробнее
          </Anchor>
        </Group>
      ) : (
        <Text c="dimmed">Синков ещё не было</Text>
      )}
    </StatCard>
  );
}

export function ClubOverviewPage() {
  const clubId = useClubId();
  const stats = useGetClubStats(clubId);
  return (
    <>
      <PageHeader title="Обзор" />
      <QueryState data={stats.data} error={stats.error} isPending={stats.isPending}>
        {(data) => (
          <Stack gap="md">
            <CurrentBlock current={data.current_block} />
            <LastSync clubId={clubId} sync={data.last_sync} />
          </Stack>
        )}
      </QueryState>
    </>
  );
}

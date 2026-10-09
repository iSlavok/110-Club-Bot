import { Alert, Group, List, Paper, Table, Text, Title } from '@mantine/core';

import { Can } from '@/entities/session';
import { describeIssue, SyncChanges, SyncStatusBadge } from '@/entities/sheet-sync';
import { SyncClubButton } from '@/features/sheet-sync';
import {
  useGetClub,
  useGetClubStats,
  useListClubSyncsInfinite,
  type ClubResponse,
  type SheetSyncResponse,
} from '@/shared/api';
import { useClubId } from '@/shared/lib/club-id';
import { formatDateTime } from '@/shared/lib/dates';
import { infinitePage, PER_PAGE, useInfinitePage } from '@/shared/lib/infinite-page';
import { InfiniteList } from '@/shared/ui/InfiniteList';
import { PageHeader } from '@/shared/ui/PageHeader';
import { QueryState } from '@/shared/ui/QueryState';

function isSyncable(club: ClubResponse): boolean {
  return club.is_active && club.spreadsheet_id !== null && club.sheet_name !== null;
}

function LastSync({ sync }: { sync: SheetSyncResponse | null }) {
  if (!sync) {
    return <Text c="dimmed">Синков ещё не было</Text>;
  }
  return (
    <>
      <Group gap="lg" mb={sync.error || sync.issues.length > 0 ? 'md' : 0}>
        <Text>Последний синк: {formatDateTime(sync.finished_at)}</Text>
        <SyncStatusBadge status={sync.status} />
        {sync.status === 'ok' && <SyncChanges sync={sync} />}
      </Group>
      {sync.error && (
        <Alert color="red" title="Таблицу прочитать не удалось">
          {sync.error}
        </Alert>
      )}
      {sync.issues.length > 0 && (
        <>
          <Text fw={500} mb="xs">
            Проблемы в таблице: {sync.issues.length}
          </Text>
          <List size="sm" spacing={4}>
            {sync.issues.map((issue, index) => (
              <List.Item key={index}>{describeIssue(issue)}</List.Item>
            ))}
          </List>
        </>
      )}
    </>
  );
}

function SyncHistory({ clubId }: { clubId: number }) {
  const query = useListClubSyncsInfinite(clubId, { per_page: PER_PAGE }, infinitePage);
  const syncs = useInfinitePage(query);
  return (
    <InfiniteList list={syncs} emptyText="Синков ещё не было">
      {(items) => (
        <Table.ScrollContainer minWidth={600}>
          <Table verticalSpacing="xs">
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Время (МСК)</Table.Th>
                <Table.Th>Статус</Table.Th>
                <Table.Th>Изменения</Table.Th>
                <Table.Th>Проблем</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {items.map((sync) => (
                <Table.Tr key={sync.id}>
                  <Table.Td>{formatDateTime(sync.finished_at)}</Table.Td>
                  <Table.Td>
                    <SyncStatusBadge status={sync.status} />
                  </Table.Td>
                  <Table.Td>
                    {sync.status === 'ok' ? (
                      <SyncChanges sync={sync} />
                    ) : (
                      <Text size="sm" c="dimmed" lineClamp={1} title={sync.error ?? undefined}>
                        {sync.error}
                      </Text>
                    )}
                  </Table.Td>
                  <Table.Td>{sync.issues.length}</Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        </Table.ScrollContainer>
      )}
    </InfiniteList>
  );
}

export function ClubSyncPage() {
  const clubId = useClubId();
  const club = useGetClub(clubId);
  const stats = useGetClubStats(clubId);
  const notSyncable = club.data !== undefined && !isSyncable(club.data);
  return (
    <>
      <PageHeader
        title="Синк таблицы"
        actions={
          <Can permission="sync.run">
            <SyncClubButton clubId={clubId} disabled={club.data === undefined || notSyncable} />
          </Can>
        }
      />
      <Paper withBorder radius="md" p="md" mb="xl">
        {notSyncable && (
          <Text c="dimmed" mb="sm">
            Синк идёт только у включённых клубов с указанными таблицей и листом.
          </Text>
        )}
        <QueryState data={stats.data} error={stats.error} isPending={stats.isPending}>
          {(data) => <LastSync sync={data.last_sync} />}
        </QueryState>
        <Text size="sm" c="dimmed" mt="md">
          Кто пропал из таблицы, остаётся в блоке, пока владелец не подтвердит удаление в чате
          алертов.
        </Text>
      </Paper>
      <Title order={4} mb="sm">
        История
      </Title>
      <SyncHistory clubId={clubId} />
    </>
  );
}

import { Anchor, Table, Text, TextInput } from '@mantine/core';
import { useDebouncedValue } from '@mantine/hooks';
import { IconSearch } from '@tabler/icons-react';
import { useState } from 'react';

import { useListUsers } from '@/shared/api';
import { formatDateTime } from '@/shared/lib/dates';
import { usePage } from '@/shared/lib/use-page';
import { PageHeader } from '@/shared/ui/PageHeader';
import { QueryState } from '@/shared/ui/QueryState';
import { TablePagination } from '@/shared/ui/TablePagination';

export function UsersPage() {
  const page = usePage();
  const [search, setSearch] = useState('');
  const [query] = useDebouncedValue(search.trim(), 300);
  const users = useListUsers({ ...page.params, q: query || undefined });

  return (
    <>
      <PageHeader title="Пользователи бота" />
      <TextInput
        mb="md"
        maw={420}
        leftSection={<IconSearch size={16} />}
        placeholder="Имя, username, Telegram или VK id"
        aria-label="Поиск"
        value={search}
        onChange={(event) => {
          setSearch(event.currentTarget.value);
          page.setPage(1);
        }}
      />
      <QueryState data={users.data} error={users.error} isPending={users.isPending}>
        {(data) => (
          <>
            <Table.ScrollContainer minWidth={700}>
              <Table verticalSpacing="sm">
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Имя</Table.Th>
                    <Table.Th>Telegram</Table.Th>
                    <Table.Th>VK</Table.Th>
                    <Table.Th>Первый /start</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {data.items.map((user) => (
                    <Table.Tr key={user.id}>
                      <Table.Td fw={500}>{user.full_name}</Table.Td>
                      <Table.Td>
                        {user.tg_username ? (
                          <Anchor
                            href={`https://t.me/${user.tg_username}`}
                            target="_blank"
                            rel="noreferrer"
                          >
                            @{user.tg_username}
                          </Anchor>
                        ) : (
                          <Text c="dimmed">{user.tg_id}</Text>
                        )}
                      </Table.Td>
                      <Table.Td>
                        {user.vk_id ? (
                          <Anchor
                            href={`https://vk.com/id${user.vk_id}`}
                            target="_blank"
                            rel="noreferrer"
                          >
                            id{user.vk_id}
                          </Anchor>
                        ) : (
                          <Text c="dimmed">не привязан</Text>
                        )}
                      </Table.Td>
                      <Table.Td>{formatDateTime(user.created_at)}</Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            </Table.ScrollContainer>
            {data.items.length === 0 && (
              <Text c="dimmed" ta="center" py="xl">
                Никого не нашли
              </Text>
            )}
            <TablePagination state={page} result={data} />
          </>
        )}
      </QueryState>
    </>
  );
}

import { Anchor, Table, Text, TextInput } from '@mantine/core';
import { useDebouncedValue } from '@mantine/hooks';
import { IconSearch } from '@tabler/icons-react';
import { useState } from 'react';

import { useListUsersInfinite } from '@/shared/api';
import { formatDateTime } from '@/shared/lib/dates';
import { infinitePage, PER_PAGE, useInfinitePage } from '@/shared/lib/infinite-page';
import { InfiniteList } from '@/shared/ui/InfiniteList';
import { PageHeader } from '@/shared/ui/PageHeader';

export function UsersPage() {
  const [search, setSearch] = useState('');
  const [debounced] = useDebouncedValue(search.trim(), 300);
  const query = useListUsersInfinite(
    { per_page: PER_PAGE, q: debounced || undefined },
    infinitePage,
  );
  const users = useInfinitePage(query);

  return (
    <>
      <PageHeader title="Пользователи бота" />
      <InfiniteList
        list={users}
        emptyText="Никого не нашли"
        filters={
          <TextInput
            w={420}
            maw="100%"
            leftSection={<IconSearch size={16} />}
            placeholder="Имя, username, Telegram или VK id"
            aria-label="Поиск"
            value={search}
            onChange={(event) => {
              setSearch(event.currentTarget.value);
            }}
          />
        }
      >
        {(items) => (
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
                {items.map((user) => (
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
        )}
      </InfiniteList>
    </>
  );
}

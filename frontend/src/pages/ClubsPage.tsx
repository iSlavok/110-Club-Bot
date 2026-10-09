import { Badge, Button, Table, Text } from '@mantine/core';
import { IconPlus } from '@tabler/icons-react';
import { useState } from 'react';
import { useNavigate } from 'react-router';

import { Can } from '@/entities/session';
import { ClubFormModal } from '@/features/club';
import { useListClubsInfinite } from '@/shared/api';
import { routes } from '@/shared/config/routes';
import { infinitePage, PER_PAGE, useInfinitePage } from '@/shared/lib/infinite-page';
import { InfiniteList } from '@/shared/ui/InfiniteList';
import { PageHeader } from '@/shared/ui/PageHeader';

export function ClubsPage() {
  const navigate = useNavigate();
  const query = useListClubsInfinite({ per_page: PER_PAGE }, infinitePage);
  const clubs = useInfinitePage(query);
  const [creating, setCreating] = useState(false);

  return (
    <>
      <PageHeader
        title="Клубы"
        actions={
          <Can permission="clubs.edit">
            <Button
              leftSection={<IconPlus size={16} />}
              onClick={() => {
                setCreating(true);
              }}
            >
              Новый клуб
            </Button>
          </Can>
        }
      />
      <InfiniteList list={clubs} emptyText="Клубов пока нет">
        {(items) => (
          <Table.ScrollContainer minWidth={600}>
            <Table highlightOnHover verticalSpacing="sm">
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Название</Table.Th>
                  <Table.Th>Чат</Table.Th>
                  <Table.Th>Лист таблицы</Table.Th>
                  <Table.Th>Статус</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {items.map((club) => (
                  <Table.Tr
                    key={club.id}
                    style={{ cursor: 'pointer' }}
                    onClick={() => {
                      void navigate(routes.club(club.id));
                    }}
                  >
                    <Table.Td fw={500}>{club.title}</Table.Td>
                    <Table.Td>{club.chat_id ?? <Text c="dimmed">—</Text>}</Table.Td>
                    <Table.Td>{club.sheet_name ?? <Text c="dimmed">—</Text>}</Table.Td>
                    <Table.Td>
                      <Badge color={club.is_active ? 'teal' : 'gray'} variant="light">
                        {club.is_active ? 'Активен' : 'Выключен'}
                      </Badge>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Table.ScrollContainer>
        )}
      </InfiniteList>
      {creating && (
        <ClubFormModal
          opened
          onClose={() => {
            setCreating(false);
          }}
        />
      )}
    </>
  );
}

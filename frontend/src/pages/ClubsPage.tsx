import { Badge, Button, Table, Text } from '@mantine/core';
import { IconPlus } from '@tabler/icons-react';
import { useState } from 'react';
import { useNavigate } from 'react-router';

import { Can } from '@/entities/session';
import { ClubFormModal } from '@/features/club';
import { useListClubs } from '@/shared/api';
import { routes } from '@/shared/config/routes';
import { usePage } from '@/shared/lib/use-page';
import { PageHeader } from '@/shared/ui/PageHeader';
import { QueryState } from '@/shared/ui/QueryState';
import { TablePagination } from '@/shared/ui/TablePagination';

export function ClubsPage() {
  const navigate = useNavigate();
  const page = usePage();
  const clubs = useListClubs(page.params);
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
      <QueryState data={clubs.data} error={clubs.error} isPending={clubs.isPending}>
        {(data) => (
          <>
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
                  {data.items.map((club) => (
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
            {data.items.length === 0 && (
              <Text c="dimmed" ta="center" py="xl">
                Клубов пока нет
              </Text>
            )}
            <TablePagination state={page} result={data} />
          </>
        )}
      </QueryState>
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

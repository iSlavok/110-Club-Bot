import { Anchor, Modal, Table, Text } from '@mantine/core';

import { useListBlockMembersInfinite, type BlockResponse } from '@/shared/api';
import { infinitePage, PER_PAGE, useInfinitePage } from '@/shared/lib/infinite-page';
import { InfiniteList } from '@/shared/ui/InfiniteList';

interface BlockMembersModalProps {
  opened: boolean;
  onClose: () => void;
  block: BlockResponse;
}

export function BlockMembersModal({ opened, onClose, block }: BlockMembersModalProps) {
  const query = useListBlockMembersInfinite(block.id, { per_page: PER_PAGE }, infinitePage);
  const members = useInfinitePage(query);
  return (
    <Modal opened={opened} onClose={onClose} title={`Участники: ${block.title}`} size="lg">
      <InfiniteList
        list={members}
        emptyText="В блоке пока никого: столбец не отмечен в таблице или синка ещё не было"
      >
        {(items) => (
          <Table verticalSpacing="xs">
            <Table.Thead>
              <Table.Tr>
                <Table.Th>VK</Table.Th>
                <Table.Th>Пользователь бота</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {items.map((member) => (
                <Table.Tr key={member.vk_id}>
                  <Table.Td>
                    <Anchor
                      href={`https://vk.com/id${member.vk_id}`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      id{member.vk_id}
                    </Anchor>
                  </Table.Td>
                  <Table.Td>
                    {member.user ? (
                      <>
                        {member.user.full_name}
                        {member.user.tg_username && (
                          <Text span c="dimmed">
                            {' '}
                            @{member.user.tg_username}
                          </Text>
                        )}
                      </>
                    ) : (
                      <Text c="dimmed">не подключил бота</Text>
                    )}
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        )}
      </InfiniteList>
    </Modal>
  );
}

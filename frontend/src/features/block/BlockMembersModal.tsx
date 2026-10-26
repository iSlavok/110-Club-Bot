import { Anchor, Modal, Table, Text } from '@mantine/core';

import { useState } from 'react';

import { ChatStatusBadge } from '@/entities/chat-access';
import {
  useListBlockMembersInfinite,
  type BlockMemberSort,
  type BlockResponse,
  type SortOrder,
} from '@/shared/api';
import { infinitePage, PER_PAGE, useInfinitePage } from '@/shared/lib/infinite-page';
import { InfiniteList } from '@/shared/ui/InfiniteList';
import { SortableTh } from '@/shared/ui/SortableTh';

interface BlockMembersModalProps {
  opened: boolean;
  onClose: () => void;
  block: BlockResponse;
}

export function BlockMembersModal({ opened, onClose, block }: BlockMembersModalProps) {
  const [sorting, setSorting] = useState<{ sort: BlockMemberSort; order: SortOrder }>({
    sort: 'bot',
    order: 'asc',
  });
  const query = useListBlockMembersInfinite(
    block.id,
    { per_page: PER_PAGE, ...sorting },
    infinitePage,
  );
  const members = useInfinitePage(query);
  return (
    <Modal opened={opened} onClose={onClose} title={`Участники блока ${block.title}`} size="lg">
      <InfiniteList
        list={members}
        emptyText="В блоке пока никого: столбец не отмечен в таблице или синка ещё не было"
      >
        {(items) => (
          <Table verticalSpacing="xs" layout="fixed" style={{ overflowWrap: 'anywhere' }}>
            <Table.Thead>
              <Table.Tr>
                <SortableTh sort="vk" current={sorting} onSort={setSorting} w={130}>
                  ВК
                </SortableTh>
                <SortableTh sort="bot" current={sorting} onSort={setSorting}>
                  Пользователь бота
                </SortableTh>
                <SortableTh sort="chat" current={sorting} onSort={setSorting} w={130}>
                  Чат
                </SortableTh>
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
                  <Table.Td>
                    {member.user?.chat_status ? (
                      <ChatStatusBadge status={member.user.chat_status} />
                    ) : (
                      <Text c="dimmed">—</Text>
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

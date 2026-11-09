import { Anchor, Group, SegmentedControl, Table, Text, TextInput } from '@mantine/core';
import { useDebouncedValue } from '@mantine/hooks';
import { IconArrowLeft, IconSearch } from '@tabler/icons-react';
import { useState } from 'react';
import { Link, useParams } from 'react-router';

import { BlockStatusBadge } from '@/entities/block';
import { ChatStatusBadge } from '@/entities/chat-access';
import { BotBlockedBadge, TelegramLink } from '@/entities/user';
import {
  getExportBlockMembersUrl,
  useGetBlock,
  useGetBlockMemberFunnel,
  useListBlockMembersInfinite,
  type BlockMemberFunnelResponse,
  type BlockMemberSort,
  type BlockMemberState,
  type BlockResponse,
  type SortOrder,
} from '@/shared/api';
import { routes } from '@/shared/config/routes';
import { useClubId } from '@/shared/lib/club-id';
import { formatDateTime } from '@/shared/lib/dates';
import { infinitePage, PER_PAGE, useInfinitePage } from '@/shared/lib/infinite-page';
import { DownloadButton } from '@/shared/ui/DownloadButton';
import { InfiniteList } from '@/shared/ui/InfiniteList';
import { PageHeader } from '@/shared/ui/PageHeader';
import { QueryState } from '@/shared/ui/QueryState';
import { SortableTh } from '@/shared/ui/SortableTh';

type StateFilter = BlockMemberState | 'all';

function stateOptions(funnel: BlockMemberFunnelResponse | undefined) {
  const count = (value: number) => (funnel ? ` · ${String(value)}` : '');
  const total = funnel?.total ?? 0;
  const withBot = funnel?.with_bot ?? 0;
  const inChat = funnel?.in_chat ?? 0;
  const botBlocked = funnel?.bot_blocked ?? 0;
  return [
    { value: 'all', label: `Все${count(total)}` },
    { value: 'in_chat', label: `В чате${count(inChat)}` },
    { value: 'not_in_chat', label: `Не в чате${count(total - inChat)}` },
    { value: 'no_bot', label: `Без бота${count(total - withBot)}` },
    { value: 'not_joined', label: `С ботом, не в чате${count(withBot - inChat - botBlocked)}` },
    { value: 'bot_blocked', label: `Заблокировали бота${count(botBlocked)}` },
  ];
}

export function ClubBlockPage() {
  const clubId = useClubId();
  const blockId = Number(useParams().blockId);
  const block = useGetBlock(blockId);
  return (
    <>
      <Anchor component={Link} to={routes.clubBlocks(clubId)} size="sm">
        <Group gap={4}>
          <IconArrowLeft size={14} />
          Все блоки
        </Group>
      </Anchor>
      <QueryState data={block.data} error={block.error} isPending={block.isPending}>
        {(data) => <BlockMembers block={data} />}
      </QueryState>
    </>
  );
}

function BlockMembers({ block }: { block: BlockResponse }) {
  const [state, setState] = useState<StateFilter>('all');
  const [search, setSearch] = useState('');
  const [debounced] = useDebouncedValue(search.trim(), 300);
  const [sorting, setSorting] = useState<{ sort: BlockMemberSort; order: SortOrder }>({
    sort: 'bot',
    order: 'asc',
  });
  const funnel = useGetBlockMemberFunnel(block.id);
  const filters = { state: state === 'all' ? undefined : state, q: debounced || undefined };
  const query = useListBlockMembersInfinite(
    block.id,
    { per_page: PER_PAGE, ...sorting, ...filters },
    infinitePage,
  );
  const members = useInfinitePage(query);

  return (
    <>
      <PageHeader
        title={
          <Group gap="sm" component="span">
            {block.title}
            <BlockStatusBadge block={block} />
          </Group>
        }
        actions={<DownloadButton href={getExportBlockMembersUrl(block.id, filters)} />}
      />
      <Text size="sm" c="dimmed" mb="md">
        {formatDateTime(block.starts_at)} — {formatDateTime(block.ends_at)}, столбец «
        {block.sheet_column_title}». Статус чата известен у тех, кого впустил бот.
      </Text>
      <InfiniteList
        list={members}
        emptyText="Никого: столбец не отмечен в таблице, синка ещё не было или фильтр никого не нашёл"
        filters={
          <>
            <SegmentedControl
              aria-label="Кто"
              data={stateOptions(funnel.data)}
              value={state}
              onChange={(value) => {
                setState(value as StateFilter);
              }}
            />
            <TextInput
              w={320}
              maw="100%"
              leftSection={<IconSearch size={16} />}
              placeholder="Имя, username, Telegram или VK ID"
              aria-label="Поиск"
              value={search}
              onChange={(event) => {
                setSearch(event.currentTarget.value);
              }}
            />
          </>
        }
      >
        {(items) => (
          <Table.ScrollContainer minWidth={760}>
            <Table verticalSpacing="sm" layout="fixed" style={{ overflowWrap: 'anywhere' }}>
              <Table.Thead>
                <Table.Tr>
                  <SortableTh sort="vk" current={sorting} onSort={setSorting} w={150}>
                    ВК
                  </SortableTh>
                  <SortableTh sort="bot" current={sorting} onSort={setSorting}>
                    Пользователь бота
                  </SortableTh>
                  <Table.Th w={240}>Telegram</Table.Th>
                  <SortableTh sort="chat" current={sorting} onSort={setSorting} w={140}>
                    Чат
                  </SortableTh>
                  <Table.Th w={160}>Зашёл в чат</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {items.map((member) => (
                  <Table.Tr key={member.vk_id}>
                    <Table.Td>
                      <Anchor
                        href={`https://vk.com/id${String(member.vk_id)}`}
                        target="_blank"
                        rel="noreferrer"
                      >
                        id{member.vk_id}
                      </Anchor>
                    </Table.Td>
                    <Table.Td fw={member.user ? 500 : undefined}>
                      {member.user ? (
                        <Group gap="xs" wrap="nowrap">
                          {member.user.full_name}
                          {member.user.bot_blocked_at && (
                            <BotBlockedBadge blockedAt={member.user.bot_blocked_at} />
                          )}
                        </Group>
                      ) : (
                        <Text c="dimmed">не подключил бота</Text>
                      )}
                    </Table.Td>
                    <Table.Td>
                      {member.user?.tg_username ? (
                        <TelegramLink username={member.user.tg_username} />
                      ) : (
                        <Text c="dimmed">—</Text>
                      )}
                    </Table.Td>
                    <Table.Td>
                      {member.user?.chat_status ? (
                        <ChatStatusBadge status={member.user.chat_status} />
                      ) : (
                        <Text c="dimmed">—</Text>
                      )}
                    </Table.Td>
                    <Table.Td>
                      {member.user?.chat_joined_at ? (
                        formatDateTime(member.user.chat_joined_at)
                      ) : (
                        <Text c="dimmed">—</Text>
                      )}
                    </Table.Td>
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

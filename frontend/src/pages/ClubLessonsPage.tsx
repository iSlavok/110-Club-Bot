import { Anchor, Badge, Button, Checkbox, SegmentedControl, Table, Text } from '@mantine/core';
import { IconPlus } from '@tabler/icons-react';
import { useState } from 'react';
import { Link } from 'react-router';

import { LESSON_KIND_LABELS } from '@/entities/lesson';
import { Can } from '@/entities/session';
import { LessonFormModal } from '@/features/lesson';
import { useListLessonsInfinite, type LessonView } from '@/shared/api';
import { routes } from '@/shared/config/routes';
import { useClubId } from '@/shared/lib/club-id';
import { formatDateTime } from '@/shared/lib/dates';
import { infinitePage, PER_PAGE, useInfinitePage } from '@/shared/lib/infinite-page';
import { InfiniteList } from '@/shared/ui/InfiniteList';
import { PageHeader } from '@/shared/ui/PageHeader';

const VIEWS: { value: LessonView; label: string }[] = [
  { value: 'upcoming', label: 'Предстоящие' },
  { value: 'past', label: 'Прошедшие' },
  { value: 'all', label: 'Все' },
];

export function ClubLessonsPage() {
  const clubId = useClubId();
  const [view, setView] = useState<LessonView>('upcoming');
  const [includeCancelled, setIncludeCancelled] = useState(false);
  const [creating, setCreating] = useState(false);
  const query = useListLessonsInfinite(
    clubId,
    { per_page: PER_PAGE, view, include_cancelled: includeCancelled || undefined },
    infinitePage,
  );
  const lessons = useInfinitePage(query);

  return (
    <>
      <PageHeader
        title="Уроки"
        actions={
          <Can permission="lessons.edit">
            <Button
              leftSection={<IconPlus size={16} />}
              onClick={() => {
                setCreating(true);
              }}
            >
              Новый урок
            </Button>
          </Can>
        }
      />
      <InfiniteList
        list={lessons}
        emptyText="Уроков нет"
        filters={
          <>
            <SegmentedControl
              aria-label="Какие уроки"
              data={VIEWS}
              value={view}
              onChange={setView}
            />
            <Checkbox
              label="Отменённые"
              checked={includeCancelled}
              onChange={(event) => {
                setIncludeCancelled(event.currentTarget.checked);
              }}
              mb={8}
            />
          </>
        }
      >
        {(items) => (
          <Table.ScrollContainer minWidth={760}>
            <Table verticalSpacing="sm">
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Начало (МСК)</Table.Th>
                  <Table.Th>Тема</Table.Th>
                  <Table.Th>Тип</Table.Th>
                  <Table.Th>Дедлайн ДЗ (МСК)</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {items.map((lesson) => (
                  <Table.Tr key={lesson.id}>
                    <Table.Td>{formatDateTime(lesson.starts_at)}</Table.Td>
                    <Table.Td>
                      <Anchor component={Link} to={routes.clubLesson(clubId, lesson.id)} fw={500}>
                        {lesson.title}
                      </Anchor>{' '}
                      {lesson.is_cancelled && (
                        <Badge color="gray" variant="light">
                          Отменён
                        </Badge>
                      )}
                    </Table.Td>
                    <Table.Td>{LESSON_KIND_LABELS[lesson.kind]}</Table.Td>
                    <Table.Td>
                      {lesson.homework_deadline_at ? (
                        formatDateTime(lesson.homework_deadline_at)
                      ) : (
                        <Text c="dimmed">нет ДЗ</Text>
                      )}
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Table.ScrollContainer>
        )}
      </InfiniteList>
      {creating && (
        <LessonFormModal
          clubId={clubId}
          onClose={() => {
            setCreating(false);
          }}
        />
      )}
    </>
  );
}

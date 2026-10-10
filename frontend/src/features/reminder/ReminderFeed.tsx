import {
  Button,
  Checkbox,
  Group,
  SegmentedControl,
  Select,
  Stack,
  Table,
  Text,
} from '@mantine/core';
import { useState } from 'react';

import { LESSON_KIND_LABELS } from '@/entities/lesson';
import { REMINDER_KIND_LABELS, ReminderStatusBadge } from '@/entities/reminder';
import { Can } from '@/entities/session';
import {
  useListLessons,
  useListRemindersInfinite,
  type ReminderResponse,
  type ReminderView,
} from '@/shared/api';
import { formatDateTime } from '@/shared/lib/dates';
import { infinitePage, PER_PAGE, useInfinitePage } from '@/shared/lib/infinite-page';
import { InfiniteList } from '@/shared/ui/InfiniteList';

import { ReminderPreviewModal } from './ReminderPreviewModal';
import { useCancelReminderConfirm } from './useCancelReminderConfirm';

const VIEWS: { value: ReminderView; label: string }[] = [
  { value: 'pending', label: 'Ожидают' },
  { value: 'sent', label: 'Отправленные' },
  { value: 'all', label: 'Все' },
];

// The lesson filter offers the latest lessons of the club; older ones are reached from their card.
const LESSON_OPTIONS_LIMIT = 200;

interface ReminderFeedProps {
  clubId: number;
  /** Fixed lesson (the lesson card): no lesson column and no lesson filter. */
  lessonId?: number;
}

export function ReminderFeed({ clubId, lessonId }: ReminderFeedProps) {
  const [view, setView] = useState<ReminderView>('pending');
  const [includeCancelled, setIncludeCancelled] = useState(false);
  const [lessonFilter, setLessonFilter] = useState<string | null>(null);
  const [previewId, setPreviewId] = useState<number | null>(null);
  const confirmCancel = useCancelReminderConfirm();
  const selectedLesson = lessonId ?? (lessonFilter ? Number(lessonFilter) : undefined);
  const query = useListRemindersInfinite(
    clubId,
    {
      per_page: PER_PAGE,
      view,
      include_cancelled: view === 'sent' ? undefined : includeCancelled || undefined,
      lesson_id: selectedLesson,
    },
    infinitePage,
  );
  const reminders = useInfinitePage(query);

  return (
    <>
      <InfiniteList
        list={reminders}
        emptyText="Напоминаний нет"
        filters={
          <>
            <SegmentedControl
              aria-label="Какие напоминания"
              data={VIEWS}
              value={view}
              onChange={(value) => {
                setView(value);
              }}
            />
            <Checkbox
              label="Отменённые"
              checked={includeCancelled}
              disabled={view === 'sent'}
              onChange={(event) => {
                setIncludeCancelled(event.currentTarget.checked);
              }}
              mb={8}
            />
            {lessonId === undefined && (
              <LessonFilter clubId={clubId} value={lessonFilter} onChange={setLessonFilter} />
            )}
          </>
        }
      >
        {(items) => (
          <Table.ScrollContainer minWidth={lessonId === undefined ? 860 : 640}>
            <Table verticalSpacing="sm">
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Когда (МСК)</Table.Th>
                  {lessonId === undefined && <Table.Th>Урок</Table.Th>}
                  <Table.Th>Что</Table.Th>
                  <Table.Th>Статус</Table.Th>
                  <Table.Th />
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {items.map((reminder) => (
                  <ReminderRow
                    key={reminder.id}
                    reminder={reminder}
                    showLesson={lessonId === undefined}
                    onPreview={() => {
                      setPreviewId(reminder.id);
                    }}
                    onCancel={() => {
                      confirmCancel(reminder);
                    }}
                  />
                ))}
              </Table.Tbody>
            </Table>
          </Table.ScrollContainer>
        )}
      </InfiniteList>
      {previewId !== null && (
        <ReminderPreviewModal
          reminderId={previewId}
          onClose={() => {
            setPreviewId(null);
          }}
        />
      )}
    </>
  );
}

interface ReminderRowProps {
  reminder: ReminderResponse;
  showLesson: boolean;
  onPreview: () => void;
  onCancel: () => void;
}

function ReminderRow({ reminder, showLesson, onPreview, onCancel }: ReminderRowProps) {
  const { lesson } = reminder;
  return (
    <Table.Tr>
      <Table.Td>{formatDateTime(reminder.sent_at ?? reminder.send_at)}</Table.Td>
      {showLesson && (
        <Table.Td>
          <Text size="sm" fw={500}>
            {lesson.title}
          </Text>
          <Text size="xs" c="dimmed">
            {LESSON_KIND_LABELS[lesson.kind]}, {formatDateTime(lesson.starts_at)}
            {lesson.is_cancelled && ' · отменён'}
          </Text>
        </Table.Td>
      )}
      <Table.Td>{REMINDER_KIND_LABELS[reminder.kind]}</Table.Td>
      <Table.Td>
        <Stack gap={2}>
          <ReminderStatusBadge status={reminder.status} />
          {reminder.error && (
            <Text size="xs" c="dimmed">
              {reminder.error}
            </Text>
          )}
        </Stack>
      </Table.Td>
      <Table.Td>
        <Group gap={4} justify="flex-end" wrap="nowrap">
          <Button size="compact-sm" variant="subtle" onClick={onPreview}>
            Текст
          </Button>
          {reminder.status === 'pending' && (
            <Can permission="lessons.edit">
              <Button size="compact-sm" variant="subtle" color="red" onClick={onCancel}>
                Отменить
              </Button>
            </Can>
          )}
        </Group>
      </Table.Td>
    </Table.Tr>
  );
}

interface LessonFilterProps {
  clubId: number;
  value: string | null;
  onChange: (value: string | null) => void;
}

function LessonFilter({ clubId, value, onChange }: LessonFilterProps) {
  const lessons = useListLessons(clubId, {
    view: 'all',
    include_cancelled: true,
    per_page: LESSON_OPTIONS_LIMIT,
  });
  const options = (lessons.data?.items ?? []).map((lesson) => ({
    value: String(lesson.id),
    label: `${formatDateTime(lesson.starts_at)} — ${lesson.title}`,
  }));
  return (
    <Select
      aria-label="Урок"
      placeholder="Все уроки"
      w={360}
      maw="100%"
      data={options}
      value={value}
      onChange={onChange}
      searchable
      clearable
    />
  );
}

import { Anchor, Badge, Button, Group, Paper, SimpleGrid, Stack, Text, Title } from '@mantine/core';
import { IconArrowLeft, IconPencil } from '@tabler/icons-react';
import { useState, type ReactNode } from 'react';
import { Link, useParams } from 'react-router';

import { LESSON_KIND_LABELS } from '@/entities/lesson';
import { formatOffset } from '@/entities/reminder';
import { Can } from '@/entities/session';
import { LessonFormModal, useCancelLessonConfirm } from '@/features/lesson';
import { ReminderFeed } from '@/features/reminder';
import { useGetLesson, type LessonResponse } from '@/shared/api';
import { routes } from '@/shared/config/routes';
import { useClubId } from '@/shared/lib/club-id';
import { formatDateTime } from '@/shared/lib/dates';
import { PageHeader } from '@/shared/ui/PageHeader';
import { QueryState } from '@/shared/ui/QueryState';

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <Text size="xs" c="dimmed" tt="uppercase" fw={600}>
        {label}
      </Text>
      {children}
    </div>
  );
}

const offsets = (values: number[], zeroLabel?: string) =>
  values.length ? values.map((value) => formatOffset(value, zeroLabel)).join(', ') : 'нет';

export function ClubLessonPage() {
  const clubId = useClubId();
  const lessonId = Number(useParams().lessonId);
  const lesson = useGetLesson(lessonId);
  return (
    <>
      <Anchor component={Link} to={routes.clubLessons(clubId)} size="sm">
        <Group gap={4}>
          <IconArrowLeft size={14} />
          Все уроки
        </Group>
      </Anchor>
      <QueryState data={lesson.data} error={lesson.error} isPending={lesson.isPending}>
        {(data) => <LessonCard clubId={clubId} lesson={data} />}
      </QueryState>
    </>
  );
}

function LessonCard({ clubId, lesson }: { clubId: number; lesson: LessonResponse }) {
  const [editing, setEditing] = useState(false);
  const confirmCancel = useCancelLessonConfirm();
  return (
    <>
      <PageHeader
        title={
          <Group gap="sm" component="span">
            {lesson.title}
            {lesson.is_cancelled && (
              <Badge color="gray" variant="light" size="lg">
                Отменён
              </Badge>
            )}
          </Group>
        }
        actions={
          !lesson.is_cancelled && (
            <Can permission="lessons.edit">
              <Group gap="xs">
                <Button
                  variant="default"
                  leftSection={<IconPencil size={16} />}
                  onClick={() => {
                    setEditing(true);
                  }}
                >
                  Изменить
                </Button>
                <Button
                  color="red"
                  variant="light"
                  onClick={() => {
                    confirmCancel(lesson);
                  }}
                >
                  Отменить урок
                </Button>
              </Group>
            </Can>
          )
        }
      />
      <Paper withBorder radius="md" p="lg" mb="xl">
        <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="md">
          <Field label="Тип">{LESSON_KIND_LABELS[lesson.kind]}</Field>
          <Field label="Начало (МСК)">{formatDateTime(lesson.starts_at)}</Field>
          <Field label="Ссылка на созвон">
            {lesson.call_url ? (
              <Anchor href={lesson.call_url} target="_blank" rel="noreferrer">
                {lesson.call_url}
              </Anchor>
            ) : (
              <Text c="dimmed">нет</Text>
            )}
          </Field>
          <Field label="Напоминания">{offsets(lesson.reminder_offsets)}</Field>
          <Field label="Дедлайн ДЗ (МСК)">
            {lesson.homework_deadline_at ? (
              formatDateTime(lesson.homework_deadline_at)
            ) : (
              <Text c="dimmed">нет ДЗ</Text>
            )}
          </Field>
          {lesson.homework_deadline_at && (
            <Field label="Напоминания о ДЗ">
              {offsets(lesson.homework_reminder_offsets, 'в момент дедлайна')}
            </Field>
          )}
        </SimpleGrid>
        {lesson.description && (
          <Stack mt="md" gap={0}>
            <Field label="Описание">
              <Text style={{ whiteSpace: 'pre-wrap' }}>{lesson.description}</Text>
            </Field>
          </Stack>
        )}
      </Paper>
      <Title order={3} mb="md">
        Напоминания
      </Title>
      <ReminderFeed clubId={clubId} lessonId={lesson.id} />
      {editing && (
        <LessonFormModal
          clubId={clubId}
          lesson={lesson}
          onClose={() => {
            setEditing(false);
          }}
        />
      )}
    </>
  );
}

import {
  Alert,
  Anchor,
  Badge,
  Button,
  Divider,
  Group,
  Paper,
  Stack,
  Text,
  Title,
} from '@mantine/core';
import { IconExternalLink, IconSchool } from '@tabler/icons-react';
import type { ReactNode } from 'react';

import {
  useGetPlatformLesson,
  type PlatformHomeworkLevelResponse,
  type PlatformLessonResponse,
  type PlatformLinkResponse,
} from '@/shared/api';
import { formatDateTime, formatShortDateTime, formatTime } from '@/shared/lib/dates';
import { errorMessage } from '@/shared/lib/errors';

import { formatDuration, sameMinute, teacherLessonUrl } from './model';

interface PlatformLessonCardProps {
  lessonId: number;
  /** The club's platform course: «Открыть» leads to the lesson in the platform admin; null: no button. */
  courseId: number | null;
  /** What the form has now, UTC; a different platform value is offered with a «Взять» button. */
  startsAt: string | null;
  deadline: string | null;
  /** null: the form has a regular lesson, not a call. */
  callUrl: string | null;
  onTakeStart: (iso: string) => void;
  onTakeDeadline: (iso: string) => void;
  onTakeCall: (url: string) => void;
}

export function PlatformLessonCard({ lessonId, ...form }: PlatformLessonCardProps) {
  const lesson = useGetPlatformLesson(lessonId);
  let body;
  if (lesson.isPending) {
    body = <Text c="dimmed">Загружаю урок с платформы…</Text>;
  } else if (lesson.error) {
    body = (
      <Alert color="red" title="Урок платформы не загрузился">
        {errorMessage(lesson.error)}
      </Alert>
    );
  } else {
    body = <Card lesson={lesson.data} {...form} />;
  }
  return (
    <Paper withBorder radius="md" p="md">
      <Group gap={6} wrap="nowrap">
        <IconSchool size={16} color="var(--mantine-color-dimmed)" />
        <Text size="xs" c="dimmed" tt="uppercase" fw={700}>
          Урок на платформе
        </Text>
      </Group>
      <Divider my="sm" />
      {body}
    </Paper>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div>
      <Text size="xs" c="dimmed" tt="uppercase" fw={600}>
        {title}
      </Text>
      {children}
    </div>
  );
}

function Mismatch({ ours, onTake }: { ours: string; onTake: () => void }) {
  return (
    <Group gap="xs" mt={4}>
      <Text size="sm" c="orange">
        у нас: {ours}
      </Text>
      <Button size="compact-xs" variant="light" color="orange" onClick={onTake}>
        Взять
      </Button>
    </Group>
  );
}

function Links({ links }: { links: PlatformLinkResponse[] }) {
  return (
    <Group gap="sm">
      {links.map((link) => (
        <Anchor key={link.url} href={link.url} target="_blank" rel="noreferrer" size="sm">
          {link.title} ↗
        </Anchor>
      ))}
    </Group>
  );
}

function level(item: PlatformHomeworkLevelResponse): string {
  return [
    item.title,
    item.is_required ? 'обязательное' : 'по желанию',
    item.task_count === null ? null : `заданий: ${String(item.task_count)}`,
    item.is_trial ? 'пробник' : null,
    item.time_limit_seconds ? `на выполнение ${formatDuration(item.time_limit_seconds)}` : null,
  ]
    .filter(Boolean)
    .join(' · ');
}

function ourCall(callUrl: string | null, platformUrl: string): string | null {
  if (callUrl === null) {
    return 'обычный урок';
  }
  if (!callUrl.trim()) {
    return 'без ссылки';
  }
  return callUrl.trim() === platformUrl ? null : 'другая ссылка';
}

function Card({
  lesson,
  startsAt,
  deadline,
  courseId,
  callUrl,
  onTakeStart,
  onTakeDeadline,
  onTakeCall,
}: Omit<PlatformLessonCardProps, 'lessonId'> & { lesson: PlatformLessonResponse }) {
  const platformDeadline = lesson.homework?.deadline_at ?? null;
  const startDiffers =
    startsAt !== null && lesson.starts_at !== null && !sameMinute(startsAt, lesson.starts_at);
  const deadlineDiffers =
    platformDeadline !== null && (deadline === null || !sameMinute(deadline, platformDeadline));
  const platformCall = lesson.call_url;
  const callDiffers = platformCall === null ? null : ourCall(callUrl, platformCall);
  return (
    <Stack gap="sm">
      <div>
        <Group justify="space-between" wrap="nowrap" align="flex-start">
          <Title order={4}>{lesson.title}</Title>
          {!lesson.is_published && (
            <Badge color="yellow" variant="light">
              черновик
            </Badge>
          )}
        </Group>
        <Text size="sm" c="dimmed">
          {[lesson.module_title, lesson.course_title].filter(Boolean).join(' · ')}
        </Text>
      </div>
      <Section title="Время">
        {lesson.starts_at ? (
          <Text size="sm">
            {formatShortDateTime(lesson.starts_at)}
            {lesson.ends_at && `–${formatTime(lesson.ends_at)}`}
          </Text>
        ) : (
          <Text size="sm" c="dimmed">
            не указано
          </Text>
        )}
        {lesson.publish_at && (
          <Text size="xs" c="dimmed">
            откроется ученикам {formatDateTime(lesson.publish_at)}
          </Text>
        )}
        {startDiffers && lesson.starts_at && (
          <Mismatch
            ours={formatShortDateTime(startsAt)}
            onTake={() => {
              if (lesson.starts_at) {
                onTakeStart(lesson.starts_at);
              }
            }}
          />
        )}
        {lesson.is_stop_lesson && (
          <Badge color="red" variant="light" mt={4}>
            стоп-урок
          </Badge>
        )}
      </Section>
      {platformCall && (
        <Section title="Созвон">
          <Anchor href={platformCall} target="_blank" rel="noreferrer" size="sm">
            Zoom ↗
          </Anchor>
          {callDiffers && (
            <Mismatch
              ours={callDiffers}
              onTake={() => {
                onTakeCall(platformCall);
              }}
            />
          )}
        </Section>
      )}
      <Section title="ДЗ">
        {lesson.homework ? (
          <Stack gap={2}>
            <Text size="sm">
              {platformDeadline
                ? `дедлайн ${formatShortDateTime(platformDeadline)}`
                : 'без дедлайна'}
            </Text>
            {deadlineDiffers && platformDeadline && (
              <Mismatch
                ours={deadline ? formatShortDateTime(deadline) : 'нет ДЗ'}
                onTake={() => {
                  onTakeDeadline(platformDeadline);
                }}
              />
            )}
            {lesson.homework.summary && (
              <Text size="sm" c="dimmed">
                {lesson.homework.summary}
              </Text>
            )}
            {lesson.homework.levels.map((item) => (
              <Text size="sm" key={item.title}>
                {level(item)}
              </Text>
            ))}
          </Stack>
        ) : (
          <Text size="sm" c="dimmed">
            нет
          </Text>
        )}
      </Section>
      {lesson.webinar.length > 0 && (
        <Section title="Вебинар">
          <Links links={lesson.webinar} />
        </Section>
      )}
      {lesson.videos.length > 0 && (
        <Section title="Видео">
          <Links links={lesson.videos} />
        </Section>
      )}
      {lesson.materials.length > 0 && (
        <Section title="Материалы">
          <Links links={lesson.materials} />
        </Section>
      )}
      {lesson.notes.length > 0 && (
        <Section title="Текст урока">
          <Stack gap={4}>
            {lesson.notes.map((note, index) => (
              <Text size="sm" key={index} style={{ whiteSpace: 'pre-wrap' }}>
                {note.title && <b>{note.title} </b>}
                {note.text}
              </Text>
            ))}
          </Stack>
        </Section>
      )}
      {courseId !== null && (
        <Button
          component="a"
          href={teacherLessonUrl(courseId, lesson.id)}
          target="_blank"
          rel="noreferrer"
          variant="default"
          leftSection={<IconExternalLink size={16} />}
        >
          Открыть
        </Button>
      )}
    </Stack>
  );
}

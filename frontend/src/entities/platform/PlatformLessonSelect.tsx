import {
  Badge,
  Combobox,
  Group,
  Input,
  InputBase,
  ScrollArea,
  Text,
  useCombobox,
} from '@mantine/core';
import { useRef, useState } from 'react';

import {
  useGetClubPlatformCourse,
  type PlatformLessonOptionResponse,
  type PlatformModuleResponse,
} from '@/shared/api';
import { formatDate, formatShortDateTime } from '@/shared/lib/dates';
import { errorMessage } from '@/shared/lib/errors';

import { parseLessonId } from './model';

const NONE = 'none';

interface PlatformLessonSelectProps {
  clubId: number;
  value: number | null;
  onChange: (lessonId: number | null) => void;
  /** Our lesson being edited: its own link is not shown as taken. */
  lessonId?: number;
}

function matches(option: PlatformLessonOptionResponse, search: string): boolean {
  const id = parseLessonId(search);
  return id === null
    ? option.title.toLowerCase().includes(search.trim().toLowerCase())
    : option.id === id;
}

function filtered(modules: PlatformModuleResponse[], search: string): PlatformModuleResponse[] {
  if (!search.trim()) {
    return modules;
  }
  return modules
    .map((module) => ({
      ...module,
      lessons: module.lessons.filter((lesson) => matches(lesson, search)),
    }))
    .filter((module) => module.lessons.length > 0);
}

function linkedLabel(option: PlatformLessonOptionResponse, lessonId?: number): string | null {
  const others = option.linked.filter((linked) => linked.id !== lessonId);
  const [first] = others;
  if (!first) {
    return null;
  }
  const more = others.length > 1 ? ` и ещё ${String(others.length - 1)}` : '';
  return `привязан: «${first.title}» ${formatDate(first.starts_at)}${more}`;
}

// Links are only marked, never blocked: curators may need to link one platform lesson twice.
export function PlatformLessonSelect({
  clubId,
  value,
  onChange,
  lessonId,
}: PlatformLessonSelectProps) {
  const course = useGetClubPlatformCourse(clubId);
  const [search, setSearch] = useState('');
  const viewport = useRef<HTMLDivElement>(null);
  const target = value ?? course.data?.suggested_lesson_id ?? null;
  const combobox = useCombobox({
    onDropdownClose: () => {
      combobox.resetSelectedOption();
      setSearch('');
    },
    onDropdownOpen: () => {
      combobox.focusSearchInput();
      // After the options mount: the dropdown opens on the lesson that is likely next.
      requestAnimationFrame(() => {
        viewport.current
          ?.querySelector(`[data-lesson-id="${String(target)}"]`)
          ?.scrollIntoView({ block: 'center' });
      });
    },
  });

  const modules = course.data?.modules ?? [];
  const selected = modules
    .flatMap((module) => module.lessons)
    .find((lesson) => lesson.id === value);
  const shown = filtered(modules, search);

  let options;
  if (course.isPending) {
    options = <Combobox.Empty>Загрузка…</Combobox.Empty>;
  } else if (course.error) {
    options = <Combobox.Empty>{errorMessage(course.error)}</Combobox.Empty>;
  } else if (shown.length === 0) {
    options = <Combobox.Empty>Ничего не нашлось</Combobox.Empty>;
  } else {
    options = shown.map((module) => (
      <Combobox.Group label={module.title} key={module.id}>
        {module.lessons.map((lesson) => {
          const linked = linkedLabel(lesson, lessonId);
          return (
            <Combobox.Option
              value={String(lesson.id)}
              key={lesson.id}
              active={lesson.id === value}
              data-lesson-id={lesson.id}
            >
              <Group justify="space-between" wrap="nowrap" gap="xs">
                <div>
                  <Text size="sm">{lesson.title}</Text>
                  <Text size="xs" c="dimmed">
                    {lesson.starts_at ? formatShortDateTime(lesson.starts_at) : 'без даты'}
                    {linked && (
                      <Text span size="xs" c="teal">
                        {' · '}
                        {linked}
                      </Text>
                    )}
                  </Text>
                </div>
                {!lesson.is_published && (
                  <Badge color="yellow" variant="light" size="sm">
                    черновик
                  </Badge>
                )}
              </Group>
            </Combobox.Option>
          );
        })}
      </Combobox.Group>
    ));
  }

  return (
    <Combobox
      store={combobox}
      onOptionSubmit={(option) => {
        onChange(option === NONE ? null : Number(option));
        combobox.closeDropdown();
      }}
    >
      <Combobox.Target>
        <InputBase
          component="button"
          type="button"
          label="Урок на платформе"
          description="Напоминания получат кнопку «Открыть урок»"
          pointer
          rightSection={<Combobox.Chevron />}
          rightSectionPointerEvents="none"
          onClick={() => {
            combobox.toggleDropdown();
          }}
        >
          {selected?.title ??
            (value === null ? (
              <Input.Placeholder>— не привязан</Input.Placeholder>
            ) : (
              `Урок #${String(value)}`
            ))}
        </InputBase>
      </Combobox.Target>
      <Combobox.Dropdown>
        <Combobox.Search
          value={search}
          onChange={(event) => {
            setSearch(event.currentTarget.value);
          }}
          placeholder="Название, номер или ссылка на урок"
        />
        <Combobox.Options>
          <ScrollArea.Autosize mah={360} type="scroll" viewportRef={viewport}>
            {!search.trim() && (
              <Combobox.Option value={NONE} active={value === null}>
                <Text size="sm" c="dimmed">
                  — не привязан
                </Text>
              </Combobox.Option>
            )}
            {options}
          </ScrollArea.Autosize>
        </Combobox.Options>
      </Combobox.Dropdown>
    </Combobox>
  );
}

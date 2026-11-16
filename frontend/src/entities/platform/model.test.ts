import { describe, expect, it } from 'vitest';

import { formatDuration, parseCourseId, parseLessonId, sameMinute } from './model';

describe('parseCourseId', () => {
  it.each([
    ['4321', 4321],
    [' https://lk.100points.ru/teacher/courses/4321/modules ', 4321],
    ['lk.100points.ru/teacher/course/12', 12],
    ['https://lk.100points.ru/teacher/course/4321/lesson/50001', 4321],
    ['', null],
    ['курс', null],
    ['https://lk.100points.ru/teacher/courses', null],
    ['0', null],
    ['99999999999', null],
  ])('%s → %s', (text, id) => {
    expect(parseCourseId(text)).toBe(id);
  });
});

describe('parseLessonId', () => {
  it.each([
    ['50002', 50002],
    ['https://lk.100points.ru/student/lesson/50002', 50002],
    ['https://lk.100points.ru/teacher/lessons/50002/edit', 50002],
    ['https://lk.100points.ru/teacher/course/4321/lesson/50002', 50002],
    ['Урок 5', null],
  ])('%s → %s', (text, id) => {
    expect(parseLessonId(text)).toBe(id);
  });
});

it('compares moments to the minute', () => {
  expect(sameMinute('2026-10-13T16:00:00Z', '2026-10-13T16:00:59Z')).toBe(true);
  expect(sameMinute('2026-10-13T16:00:00Z', '2026-10-13T16:01:00Z')).toBe(false);
});

it.each([
  [600, '10 мин'],
  [10_800, '3 ч'],
  [14_100, '3 ч 55 мин'],
])('formats %i seconds as %s', (seconds, text) => {
  expect(formatDuration(seconds)).toBe(text);
});

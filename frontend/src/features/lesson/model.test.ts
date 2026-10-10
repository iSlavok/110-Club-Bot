import { describe, expect, it } from 'vitest';

import { chatNotices, homeworkRemindersBeforeStart, minutesUntil } from './model';

const START = '2026-10-03T16:00:00Z';
const DEADLINE = '2026-10-06T20:59:00Z';

describe('chatNotices', () => {
  it('is empty when neither the start nor the deadline changed', () => {
    const schedule = { starts_at: START, homework_deadline_at: DEADLINE };

    expect(chatNotices(schedule, { ...schedule, starts_at: '2026-10-03T19:00:00+03:00' })).toEqual(
      [],
    );
  });

  it('lists a new start, a moved deadline and removed homework', () => {
    expect(
      chatNotices(
        { starts_at: START, homework_deadline_at: DEADLINE },
        { starts_at: '2026-10-04T16:00:00Z', homework_deadline_at: '2026-10-07T20:59:00Z' },
      ),
    ).toEqual(['новое время урока', 'новый дедлайн ДЗ']);
    expect(
      chatNotices(
        { starts_at: START, homework_deadline_at: DEADLINE },
        { starts_at: START, homework_deadline_at: null },
      ),
    ).toEqual(['ДЗ отменено']);
  });

  it('does not offer a notice for added homework', () => {
    expect(
      chatNotices(
        { starts_at: START, homework_deadline_at: null },
        { starts_at: START, homework_deadline_at: DEADLINE },
      ),
    ).toEqual([]);
  });
});

describe('minutesUntil', () => {
  it('rounds down to whole minutes', () => {
    expect(minutesUntil(START, Date.parse(START) - 90.5 * 60_000)).toBe(90);
    expect(minutesUntil(START, Date.parse(START) + 30_000)).toBe(-1);
  });
});

describe('homeworkRemindersBeforeStart', () => {
  it('returns offsets that fire before the lesson', () => {
    expect(homeworkRemindersBeforeStart(START, '2026-10-04T16:00:00Z', [2880, 1440, 180])).toEqual([
      2880,
    ]);
    expect(homeworkRemindersBeforeStart(START, DEADLINE, [1440, 180])).toEqual([]);
  });
});

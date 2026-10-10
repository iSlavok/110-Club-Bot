import { describe, expect, it } from 'vitest';

import { formatOffset, latestFirst } from './offsets';

describe('formatOffset', () => {
  it.each([
    [1440, 'за 1 день'],
    [2880, 'за 2 дня'],
    [10080, 'за 7 дней'],
    [60, 'за 1 час'],
    [180, 'за 3 часа'],
    [1, 'за 1 минуту'],
    [45, 'за 45 минут'],
    [90, 'за 1 ч 30 мин'],
    [2817, 'за 1 д 22 ч 57 мин'],
    [1445, 'за 1 д 5 мин'],
    [0, 'в момент начала'],
  ])('%i → %s', (minutes, expected) => {
    expect(formatOffset(minutes)).toBe(expected);
  });

  it('names the zero offset by its event', () => {
    expect(formatOffset(0, 'в дедлайн')).toBe('в дедлайн');
  });
});

describe('latestFirst', () => {
  it('sorts descending and drops duplicates', () => {
    expect(latestFirst([60, 1440, 60, 0])).toEqual([1440, 60, 0]);
  });
});

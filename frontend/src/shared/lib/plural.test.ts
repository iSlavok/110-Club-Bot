import { describe, expect, it } from 'vitest';

import { plural } from './plural';

describe('plural', () => {
  it.each([
    [1, 'день'],
    [3, 'дня'],
    [5, 'дней'],
    [11, 'дней'],
    [12, 'дней'],
    [21, 'день'],
    [22, 'дня'],
    [111, 'дней'],
  ])('%i → %s', (n, expected) => {
    expect(plural(n, 'день', 'дня', 'дней')).toBe(expected);
  });
});

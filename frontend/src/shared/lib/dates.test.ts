import { describe, expect, it } from 'vitest';

import { formatDateTime, fromPickerValue, toPickerValue } from './dates';

describe('dates', () => {
  it('shows UTC instants in Moscow time', () => {
    expect(formatDateTime('2026-08-31T21:00:00Z')).toBe('01.09.2026 00:00');
  });

  it('round-trips picker values through UTC', () => {
    const iso = fromPickerValue('2026-09-01 00:00:00');

    expect(iso).toBe('2026-08-31T21:00:00.000Z');
    expect(toPickerValue(iso)).toBe('2026-09-01 00:00:00');
  });
});

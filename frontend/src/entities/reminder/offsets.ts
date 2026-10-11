import { plural } from '@/shared/lib/plural';

const MINUTES_IN_HOUR = 60;
const MINUTES_IN_DAY = 24 * MINUTES_IN_HOUR;

// Backend limits: 0 minutes to 30 days, at most 10 reminders per lesson or homework.
export const MAX_OFFSET_MINUTES = 30 * MINUTES_IN_DAY;
export const MAX_OFFSETS = 10;

export const OFFSET_PRESETS = [0, 15, 30, 60, 120, 180, 360, 720, 1440, 2880, 4320, 10080];

export const OFFSET_UNITS = [
  { value: 'minutes', label: 'минут', minutes: 1 },
  { value: 'hours', label: 'часов', minutes: MINUTES_IN_HOUR },
  { value: 'days', label: 'дней', minutes: MINUTES_IN_DAY },
] as const;

export type OffsetUnit = (typeof OFFSET_UNITS)[number]['value'];

/** 1440 → 'за 1 день', 180 → 'за 3 часа', 90 → 'за 1 ч 30 мин', 0 → zeroLabel. */
export function formatOffset(minutes: number, zeroLabel = 'в момент начала'): string {
  if (minutes === 0) {
    return zeroLabel;
  }
  if (minutes % MINUTES_IN_DAY === 0) {
    const days = minutes / MINUTES_IN_DAY;
    return `за ${days} ${plural(days, 'день', 'дня', 'дней')}`;
  }
  if (minutes % MINUTES_IN_HOUR === 0) {
    const hours = minutes / MINUTES_IN_HOUR;
    return `за ${hours} ${plural(hours, 'час', 'часа', 'часов')}`;
  }
  if (minutes < MINUTES_IN_HOUR) {
    return `за ${minutes} ${plural(minutes, 'минуту', 'минуты', 'минут')}`;
  }
  const days = Math.floor(minutes / MINUTES_IN_DAY);
  const hours = Math.floor((minutes % MINUTES_IN_DAY) / MINUTES_IN_HOUR);
  const parts = [days ? `${days} д` : '', hours ? `${hours} ч` : '', `${minutes % 60} мин`];
  return `за ${parts.filter(Boolean).join(' ')}`;
}

export function latestFirst(offsets: number[]): number[] {
  return [...new Set(offsets)].sort((a, b) => b - a);
}

import dayjs from 'dayjs';
import timezone from 'dayjs/plugin/timezone';
import utc from 'dayjs/plugin/utc';

dayjs.extend(utc);
dayjs.extend(timezone);

// Schedules are run in Moscow time; the API always speaks UTC.
export const BUSINESS_TZ = 'Europe/Moscow';

const PICKER_FORMAT = 'YYYY-MM-DD HH:mm:ss';

export function formatDateTime(iso: string): string {
  return dayjs(iso).tz(BUSINESS_TZ).format('DD.MM.YYYY HH:mm');
}

export function formatDate(iso: string): string {
  return dayjs(iso).tz(BUSINESS_TZ).format('DD.MM.YYYY');
}

/** UTC ISO string → value for Mantine date pickers, which show wall-clock Moscow time. */
export function toPickerValue(iso: string): string {
  return dayjs(iso).tz(BUSINESS_TZ).format(PICKER_FORMAT);
}

/** Mantine picker value (Moscow wall-clock time) → UTC ISO string for the API. */
export function fromPickerValue(value: string): string {
  return dayjs.tz(value, PICKER_FORMAT, BUSINESS_TZ).toISOString();
}

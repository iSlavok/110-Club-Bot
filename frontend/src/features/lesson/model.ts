const MINUTE_MS = 60_000;

export interface LessonSchedule {
  starts_at: string;
  homework_deadline_at: string | null;
}

const sameMoment = (a: string, b: string) => Date.parse(a) === Date.parse(b);

export type ChatNotice = 'rescheduled' | 'cancelled' | 'deadline_changed' | 'homework_removed';

/** Changes the chat may be told about; offsets are replanned silently and are not among them. */
export function chatNotices(before: LessonSchedule, after: LessonSchedule): ChatNotice[] {
  const notices: ChatNotice[] = [];
  if (!sameMoment(before.starts_at, after.starts_at)) {
    notices.push('rescheduled');
  }
  if (before.homework_deadline_at !== null) {
    if (after.homework_deadline_at === null) {
      notices.push('homework_removed');
    } else if (!sameMoment(before.homework_deadline_at, after.homework_deadline_at)) {
      notices.push('deadline_changed');
    }
  }
  return notices;
}

/** Whole minutes left until the moment, rounded down: the «now» offset sends right after saving. */
export function minutesUntil(iso: string, nowMs = Date.now()): number {
  return Math.floor((Date.parse(iso) - nowMs) / MINUTE_MS);
}

/** Homework offsets whose reminder would reach the chat before the lesson has even started. */
export function homeworkRemindersBeforeStart(
  startsAt: string,
  deadline: string,
  offsets: number[],
): number[] {
  const start = Date.parse(startsAt);
  return offsets.filter((offset) => Date.parse(deadline) - offset * MINUTE_MS < start);
}

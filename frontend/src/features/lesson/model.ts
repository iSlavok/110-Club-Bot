const MINUTE_MS = 60_000;

export interface LessonSchedule {
  starts_at: string;
  homework_deadline_at: string | null;
}

const sameMoment = (a: string, b: string) => Date.parse(a) === Date.parse(b);

/** Changes the chat may be told about; offsets are replanned silently and are not among them. */
export function chatNotices(before: LessonSchedule, after: LessonSchedule): string[] {
  const notices: string[] = [];
  if (!sameMoment(before.starts_at, after.starts_at)) {
    notices.push('новое время урока');
  }
  if (before.homework_deadline_at !== null) {
    if (after.homework_deadline_at === null) {
      notices.push('ДЗ отменено');
    } else if (!sameMoment(before.homework_deadline_at, after.homework_deadline_at)) {
      notices.push('новый дедлайн ДЗ');
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

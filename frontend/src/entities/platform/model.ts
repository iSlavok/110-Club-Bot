const INT32_MAX = 2_147_483_647;
const DIGITS = /^\d+$/;
const COURSE_IN_LINK = /\/courses?\/(\d+)/;
const LESSON_IN_LINK = /\/lessons?\/(\d+)/;
const MINUTE_MS = 60_000;
const PLATFORM_URL = 'https://lk.100points.ru';

function positiveId(digits: string | undefined): number | null {
  const id = Number(digits);
  return digits && id > 0 && id <= INT32_MAX ? id : null;
}

/** Course id from what an admin pastes: the course link from the platform admin or the bare id. */
export function parseCourseId(text: string): number | null {
  const value = text.trim();
  return positiveId(DIGITS.test(value) ? value : COURSE_IN_LINK.exec(value)?.[1]);
}

/** Lesson id typed or pasted into the search: the bare id or a student or admin link to the lesson. */
export function parseLessonId(text: string): number | null {
  const value = text.trim();
  return positiveId(DIGITS.test(value) ? value : LESSON_IN_LINK.exec(value)?.[1]);
}

/** The lesson in the platform admin; the platform's lesson card has no course id, so it comes from the club. */
export function teacherLessonUrl(courseId: number, lessonId: number): string {
  return `${PLATFORM_URL}/teacher/course/${String(courseId)}/lesson/${String(lessonId)}`;
}

/** The platform shows times to the minute: seconds never make a difference. */
export function sameMinute(a: string, b: string): boolean {
  return Math.floor(Date.parse(a) / MINUTE_MS) === Math.floor(Date.parse(b) / MINUTE_MS);
}

export function formatDuration(seconds: number): string {
  const minutes = Math.round(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  if (hours === 0) {
    return `${String(rest)} мин`;
  }
  return rest === 0 ? `${String(hours)} ч` : `${String(hours)} ч ${String(rest)} мин`;
}

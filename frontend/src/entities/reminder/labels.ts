import type { ReminderKind, ReminderStatus } from '@/shared/api';

export const REMINDER_KIND_LABELS: Record<ReminderKind, string> = {
  lesson_upcoming: 'Напоминание об уроке',
  lesson_starting: 'Урок начинается',
  homework_deadline: 'Дедлайн ДЗ',
  lesson_rescheduled: 'Урок перенесён',
  lesson_cancelled: 'Урок отменён',
  homework_deadline_changed: 'Дедлайн ДЗ изменён',
  homework_removed: 'ДЗ отменено',
};

export const REMINDER_STATUSES: Record<ReminderStatus, { label: string; color: string }> = {
  pending: { label: 'Ждёт', color: 'blue' },
  sent: { label: 'Отправлено', color: 'teal' },
  failed: { label: 'Ошибка', color: 'red' },
  skipped: { label: 'Пропущено', color: 'yellow' },
  cancelled: { label: 'Отменено', color: 'gray' },
};

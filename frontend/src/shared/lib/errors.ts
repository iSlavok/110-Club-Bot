import { ApiError } from '@/shared/api/http';

const MESSAGES: Record<string, string> = {
  NOT_AUTHENTICATED: 'Сессия закончилась, войдите снова.',
  PERMISSION_DENIED: 'Недостаточно прав.',
  PERMISSION_ESCALATION: 'Нельзя выдавать или менять права, которых нет у вас.',
  OWN_ACCESS_CHANGE: 'Нельзя менять свою роль или отключать себя.',
  OWNER_NOT_EDITABLE: 'Владельцы задаются на сервере и не редактируются.',
  INVALID_LOGIN_CODE: 'Код неверный или истёк. Запросите новый командой /login.',
  TOO_MANY_LOGIN_ATTEMPTS: 'Слишком много попыток. Подождите 15 минут.',
  INVALID_WIDGET_DATA: 'Telegram не подтвердил вход. Попробуйте ещё раз.',
  LOGIN_UNAVAILABLE: 'Вход временно недоступен. Попробуйте через пару минут.',
  TELEGRAM_UNAVAILABLE: 'Telegram сейчас недоступен. Попробуйте позже.',
  ADMIN_ACCESS_DENIED: 'У этого Telegram-аккаунта нет доступа к админке.',
  EMPTY_UPDATE: 'Нечего сохранять: ничего не изменилось.',
  ROLE_TITLE_TAKEN: 'Роль с таким названием уже есть.',
  ROLE_IN_USE: 'Роль назначена админам — сначала смените им роль.',
  ADMIN_ALREADY_EXISTS: 'Админ с таким Telegram id уже есть.',
  CLUB_NOT_FOUND: 'Клуб не найден.',
  CLUB_TITLE_TAKEN: 'Клуб с таким названием уже есть.',
  BLOCK_COLUMN_TAKEN: 'В этом клубе уже есть блок с таким столбцом таблицы.',
  INVALID_BLOCK_PERIOD: 'Блок должен заканчиваться позже, чем начинается.',
  BLOCK_HAS_MEMBERS: 'В блоке есть участники из таблицы — удалить нельзя.',
  VK_LINK_MODE_NOT_CONFIGURED: 'Этот способ привязки VK не настроен на сервере.',
  CLUB_NOT_SYNCABLE: 'Клуб выключен или у него не указаны таблица и лист.',
  SHEET_SYNC_DISABLED: 'Синк выключен: на сервере не настроен ключ Google.',
  VALIDATION_FAILED: 'Проверьте заполнение полей.',
};

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return MESSAGES[error.code] ?? error.message;
  }
  return 'Не удалось связаться с сервером.';
}

/** Field errors from a 422 response keyed by body field name, ready for Mantine form.setErrors. */
export function fieldErrors(error: unknown): Record<string, string> {
  if (!(error instanceof ApiError)) {
    return {};
  }
  const entries = error.fields
    .filter((field) => field.loc[0] === 'body' && field.loc.length > 1)
    .map((field) => [field.loc.slice(1).join('.'), field.message] as const);
  return Object.fromEntries(entries);
}

export function isUnauthenticated(error: unknown): boolean {
  return error instanceof ApiError && error.status === 401;
}

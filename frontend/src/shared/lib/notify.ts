import { notifications } from '@mantine/notifications';

import { errorMessage } from './errors';

export function notifySuccess(message: string): void {
  notifications.show({ color: 'teal', message });
}

export function notifyError(error: unknown): void {
  notifications.show({ color: 'red', title: 'Ошибка', message: errorMessage(error) });
}

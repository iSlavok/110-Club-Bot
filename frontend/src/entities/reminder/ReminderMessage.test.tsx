import { screen } from '@testing-library/react';
import { expect, it } from 'vitest';

import { renderWithProviders } from '@/test/render';

import { ReminderMessage } from './ReminderMessage';

it('shows the link buttons under the message as Telegram does', () => {
  renderWithProviders(
    <ReminderMessage
      html="<b>Урок «Кислоты»</b>"
      buttons={[
        { text: 'Подключиться', url: 'https://meet.example.com/abc' },
        { text: 'Открыть урок', url: 'https://lk.100points.ru/student/lesson/702' },
      ]}
    />,
  );

  expect(screen.getByRole('link', { name: 'Подключиться' })).toHaveAttribute(
    'href',
    'https://meet.example.com/abc',
  );
  expect(screen.getByRole('link', { name: 'Открыть урок' })).toHaveAttribute(
    'href',
    'https://lk.100points.ru/student/lesson/702',
  );
});

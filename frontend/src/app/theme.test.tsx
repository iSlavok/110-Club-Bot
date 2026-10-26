import { DateTimePicker } from '@mantine/dates';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import dayjs from 'dayjs';
import { describe, expect, it } from 'vitest';

import { renderWithProviders } from '@/test/render';

describe('theme', () => {
  it('marks today in date pickers', async () => {
    renderWithProviders(<DateTimePicker label="Начало" />);

    await userEvent.click(screen.getByRole('button', { name: 'Начало' }));

    const today = await screen.findByRole('button', {
      name: dayjs().locale('ru').format('D MMMM YYYY'),
    });
    expect(today).toHaveAttribute('data-today');
    expect(today).toHaveAttribute('data-highlight-today');
  });
});

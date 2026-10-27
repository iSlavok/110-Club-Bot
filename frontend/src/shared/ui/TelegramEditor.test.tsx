import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { renderWithProviders } from '@/test/render';

import { TelegramEditor } from './TelegramEditor';

describe('TelegramEditor', () => {
  it('starts from Telegram HTML and reports edits as Telegram HTML', async () => {
    const onChange = vi.fn();
    renderWithProviders(
      <TelegramEditor label="Текст" initialValue="<b>Привет</b>" onChange={onChange} />,
    );

    const box = await screen.findByRole('textbox');
    expect(box.querySelector('strong')).toHaveTextContent('Привет');
    await userEvent.click(box);
    await userEvent.keyboard('{Control>}a{/Control}');
    await userEvent.click(screen.getByRole('button', { name: 'Курсив' }));

    await waitFor(() => {
      expect(onChange).toHaveBeenLastCalledWith('<b><i>Привет</i></b>');
    });
  });

  it('offers only what Telegram can show', async () => {
    renderWithProviders(<TelegramEditor label="Текст" initialValue="" onChange={vi.fn()} />);

    await screen.findByRole('textbox');
    for (const name of [
      'Жирный',
      'Курсив',
      'Подчёркнутый',
      'Зачёркнутый',
      'Скрытый текст',
      'Ссылка',
      'Моноширинный',
      'Блок кода',
      'Цитата',
    ]) {
      expect(screen.getByRole('button', { name })).toBeInTheDocument();
    }
  });

  it('shows the field error', async () => {
    renderWithProviders(
      <TelegramEditor
        label="Текст"
        initialValue=""
        onChange={vi.fn()}
        error="Напишите сообщение"
      />,
    );

    expect(await screen.findByText('Напишите сообщение')).toBeInTheDocument();
  });
});

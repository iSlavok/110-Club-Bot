import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { describe, expect, it, vi } from 'vitest';

import { makeAdmin } from '@/test/fixtures';
import { renderWithProviders } from '@/test/render';
import { server } from '@/test/server';

import { LoginByCodeForm } from './LoginByCodeForm';

function firstDigitInput(): HTMLElement {
  const [first] = screen.getAllByRole('textbox');
  if (!first) {
    throw new Error('PinInput rendered no inputs');
  }
  return first;
}

describe('LoginByCodeForm', () => {
  it('logs in once all six digits are typed', async () => {
    let sentCode: unknown;
    server.use(
      http.post('/api/v1/auth/code', async ({ request }) => {
        sentCode = ((await request.json()) as { code: string }).code;
        return HttpResponse.json(makeAdmin());
      }),
    );
    const onSuccess = vi.fn();
    renderWithProviders(<LoginByCodeForm botUsername="club_bot" onSuccess={onSuccess} />);

    await userEvent.type(firstDigitInput(), '123456');

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalledOnce();
    });
    expect(sentCode).toBe('123456');
    expect(screen.getByRole('link', { name: '@club_bot' })).toHaveAttribute(
      'href',
      'https://t.me/club_bot',
    );
  });

  it('explains a wrong code', async () => {
    server.use(
      http.post('/api/v1/auth/code', () =>
        HttpResponse.json({ code: 'INVALID_LOGIN_CODE', message: 'wrong' }, { status: 400 }),
      ),
    );
    renderWithProviders(<LoginByCodeForm botUsername="club_bot" onSuccess={vi.fn()} />);

    await userEvent.type(firstDigitInput(), '000000');

    expect(await screen.findByText(/Код неверный или истёк/)).toBeInTheDocument();
  });
});

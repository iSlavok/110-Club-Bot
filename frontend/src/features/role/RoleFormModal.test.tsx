import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { describe, expect, it, vi } from 'vitest';

import type { PermissionResponse } from '@/shared/api';
import { renderWithProviders } from '@/test/render';
import { server } from '@/test/server';

import { RoleFormModal } from './RoleFormModal';

const CATALOG: PermissionResponse[] = [
  { code: 'clubs.view', title: 'Просмотр клубов', group: 'clubs' },
  { code: 'roles.edit', title: 'Управление ролями', group: 'admins' },
];

describe('RoleFormModal', () => {
  it('creates a role with the chosen permissions only', async () => {
    let body: unknown;
    server.use(
      http.post('/api/v1/roles', async ({ request }) => {
        body = await request.json();
        return HttpResponse.json(
          { id: 1, title: 'Куратор', permissions: ['clubs.view'] },
          { status: 201 },
        );
      }),
    );
    const onClose = vi.fn();
    renderWithProviders(
      <RoleFormModal opened onClose={onClose} catalog={CATALOG} grantable={['clubs.view']} />,
    );

    await userEvent.type(await screen.findByLabelText(/Название/), 'Куратор');
    await userEvent.click(screen.getByLabelText('Просмотр клубов'));
    await userEvent.click(screen.getByRole('button', { name: 'Сохранить' }));

    await waitFor(() => {
      expect(onClose).toHaveBeenCalledOnce();
    });
    expect(body).toEqual({ title: 'Куратор', permissions: ['clubs.view'] });
    expect(screen.getByLabelText('Управление ролями')).toBeDisabled();
  });
});

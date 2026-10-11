import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';

import { server } from '@/test/server';

import { ApiError, apiFetch } from './http';

describe('apiFetch', () => {
  it('returns parsed JSON', async () => {
    server.use(http.get('/api/v1/thing', () => HttpResponse.json({ ok: true })));

    await expect(apiFetch('/api/v1/thing', { method: 'GET' })).resolves.toEqual({ ok: true });
  });

  it('returns undefined for empty responses', async () => {
    server.use(http.delete('/api/v1/thing', () => new HttpResponse(null, { status: 204 })));

    await expect(apiFetch('/api/v1/thing', { method: 'DELETE' })).resolves.toBeUndefined();
  });

  it('turns the common error body into ApiError', async () => {
    server.use(
      http.get('/api/v1/thing', () =>
        HttpResponse.json({ code: 'CLUB_NOT_FOUND', message: 'Club 1 not found' }, { status: 404 }),
      ),
    );

    const error: unknown = await apiFetch('/api/v1/thing', { method: 'GET' }).catch(
      (e: unknown) => e,
    );

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 404, code: 'CLUB_NOT_FOUND' });
  });
});

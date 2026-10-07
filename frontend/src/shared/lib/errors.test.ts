import { describe, expect, it } from 'vitest';

import { ApiError } from '@/shared/api/http';

import { errorMessage, fieldErrors, isUnauthenticated } from './errors';

describe('errors', () => {
  it('translates known codes and falls back to the server message', () => {
    expect(errorMessage(new ApiError(409, 'ROLE_IN_USE', 'raw'))).toContain('сначала смените');
    expect(errorMessage(new ApiError(400, 'SOMETHING_NEW', 'raw message'))).toBe('raw message');
    expect(errorMessage(new TypeError('Failed to fetch'))).toBe('Не удалось связаться с сервером.');
  });

  it('maps body field errors for forms', () => {
    const error = new ApiError(422, 'VALIDATION_FAILED', 'x', [
      { loc: ['body', 'title'], message: 'too long' },
      { loc: ['query', 'limit'], message: 'ignored' },
    ]);

    expect(fieldErrors(error)).toEqual({ title: 'too long' });
  });

  it('detects expired sessions', () => {
    expect(isUnauthenticated(new ApiError(401, 'NOT_AUTHENTICATED', 'x'))).toBe(true);
    expect(isUnauthenticated(new ApiError(403, 'PERMISSION_DENIED', 'x'))).toBe(false);
  });
});

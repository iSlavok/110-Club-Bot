export interface FieldError {
  loc: (string | number)[];
  message: string;
}

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    readonly fields: FieldError[] = [],
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

interface ErrorBody {
  code?: unknown;
  message?: unknown;
  fields?: unknown;
}

function toApiError(status: number, body: unknown): ApiError {
  const { code, message, fields } = (body ?? {}) as ErrorBody;
  return new ApiError(
    status,
    typeof code === 'string' ? code : 'HTTP_ERROR',
    typeof message === 'string' ? message : `Request failed with status ${status}`,
    Array.isArray(fields) ? (fields as FieldError[]) : [],
  );
}

// Orval calls this for every generated request; the session travels in an httpOnly cookie.
export async function apiFetch<T>(url: string, options: RequestInit): Promise<T> {
  const response = await fetch(url, { ...options, credentials: 'same-origin' });
  const text = await response.text();
  const body: unknown = text ? JSON.parse(text) : undefined;
  if (!response.ok) {
    throw toApiError(response.status, body);
  }
  return body as T;
}

export type ErrorType<Error> = Error extends unknown ? ApiError : never;
export type BodyType<Body> = Body;

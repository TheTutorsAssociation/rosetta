import { apiBaseUrl } from '~/helpers/env';
import { safeGetItem } from '~/helpers/storage';
import type { User } from '~/types';

export { apiBaseUrl };

/** Error thrown by {@link apiRequest} when the response status is not ok. */
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/** Standard list response shape (snake_case `page_size` mirrors the backend). */
export type PaginatedResponse<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

/**
 * Build a human-readable message from an error response body. FastAPI sends a
 * string `detail` for most errors but an array of `{ loc, msg, type }` objects
 * for 422 validation failures; both are flattened to a string here. Falls back
 * to the HTTP status text, then a generic message.
 */
function errorMessage(body: unknown, statusText: string): string {
  const b = (body ?? {}) as { detail?: unknown; error?: unknown };
  if (typeof b.detail === 'string') return b.detail;
  if (Array.isArray(b.detail)) {
    return b.detail.map((entry: { msg: string }) => entry.msg).join('; ');
  }
  if (typeof b.error === 'string') return b.error;
  return statusText || 'Request failed';
}

/**
 * The single typed HTTP client. Injects the base URL and JSON headers, attaches
 * a bearer token from storage when present, parses the JSON body, and throws
 * {@link ApiError} on a non-ok response (message from `detail`, `error`, or the
 * status text).
 *
 * Components never call `fetch()` directly — loaders and actions call this (or a
 * resource object built on it, like {@link authApi}).
 */
export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = safeGetItem('token');
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(options.headers ?? {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  const response = await fetch(`${apiBaseUrl}${path}`, { ...options, headers });
  const body = await response.json().catch(() => null);

  if (!response.ok) {
    throw new ApiError(response.status, errorMessage(body, response.statusText));
  }

  return body as T;
}

/** Successful response from `POST /auth/login`. */
export interface LoginResponse {
  access_token: string;
  token_type: string;
}

/**
 * Auth resource client. `login` exchanges credentials for a bearer token via
 * `POST /auth/login`; `checkUser` validates the stored token by fetching the
 * signed-in user (it rejects with {@link ApiError} when the token is missing or
 * invalid). Consumed by the login route and `AuthProvider`.
 */
export const authApi = {
  login: (email: string, password: string): Promise<LoginResponse> =>
    apiRequest('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  checkUser: (): Promise<User> => apiRequest('/users/me'),
};

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
 * The single typed HTTP client. Injects the base URL and JSON headers, attaches
 * a bearer token from storage when present, parses the JSON body, and throws
 * {@link ApiError} on a non-ok response (message from `detail` or `error`).
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
    // `response.statusText` is always a (possibly empty) string, so the final fallback is unreachable.
    const message =
      body?.detail ?? body?.error ?? response.statusText ?? /* istanbul ignore next */ 'Request failed';
    throw new ApiError(response.status, message);
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

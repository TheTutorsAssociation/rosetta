import { ApiError, apiRequest, authApi, apiBaseUrl } from '~/data/api';
import { safeGetItem } from '~/helpers/storage';
import { mockUser } from '../mocks';

jest.mock('~/helpers/storage');

const mockGetItem = jest.mocked(safeGetItem);
const mockFetch = jest.fn();

function jsonResponse(body: unknown, init: ResponseInit = {}): Response {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
}

function lastCall(): [string, RequestInit] {
  return mockFetch.mock.calls.at(-1) as [string, RequestInit];
}

describe('apiRequest', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch = mockFetch as typeof fetch;
    mockGetItem.mockReturnValue(null);
  });

  it('prefixes the path with the base url', async () => {
    mockFetch.mockResolvedValue(jsonResponse({ ok: true }));
    await apiRequest('/ping');
    expect(lastCall()[0]).toBe(`${apiBaseUrl}/ping`);
  });

  it('sends a JSON content-type header', async () => {
    mockFetch.mockResolvedValue(jsonResponse({ ok: true }));
    await apiRequest('/ping');
    expect((lastCall()[1].headers as Record<string, string>)['Content-Type']).toBe(
      'application/json',
    );
  });

  it('attaches a bearer token from storage when present', async () => {
    mockGetItem.mockReturnValue('abc123');
    mockFetch.mockResolvedValue(jsonResponse({ ok: true }));
    await apiRequest('/ping');
    expect((lastCall()[1].headers as Record<string, string>).Authorization).toBe('Bearer abc123');
  });

  it('omits the Authorization header when there is no token', async () => {
    mockFetch.mockResolvedValue(jsonResponse({ ok: true }));
    await apiRequest('/ping');
    expect((lastCall()[1].headers as Record<string, string>).Authorization).toBeUndefined();
  });

  it('parses and returns the JSON body on a successful response', async () => {
    mockFetch.mockResolvedValue(jsonResponse(mockUser));
    await expect(apiRequest('/users/me')).resolves.toEqual(mockUser);
  });

  it('throws an ApiError carrying the response status on a non-ok response', async () => {
    mockFetch.mockResolvedValue(jsonResponse({ detail: 'Not found' }, { status: 404 }));
    await expect(apiRequest('/users/me')).rejects.toMatchObject({
      name: 'ApiError',
      status: 404,
    });
  });

  it('uses json.detail as the error message when present', async () => {
    mockFetch.mockResolvedValue(jsonResponse({ detail: 'Boom detail' }, { status: 500 }));
    await expect(apiRequest('/ping')).rejects.toThrow('Boom detail');
  });

  it('falls back to json.error when detail is absent', async () => {
    mockFetch.mockResolvedValue(jsonResponse({ error: 'Boom error' }, { status: 400 }));
    await expect(apiRequest('/ping')).rejects.toThrow('Boom error');
  });

  it('falls back to the status text when the error body has neither detail nor error', async () => {
    mockFetch.mockResolvedValue(
      new Response('not json', { status: 503, statusText: 'Service Unavailable' }),
    );
    await expect(apiRequest('/ping')).rejects.toThrow('Service Unavailable');
  });

  it('flattens a FastAPI 422 detail array into one message', async () => {
    mockFetch.mockResolvedValue(
      jsonResponse(
        {
          detail: [
            { loc: ['body', 'password'], msg: 'password too long', type: 'string_too_long' },
            { loc: ['body', 'email'], msg: 'not a valid email', type: 'value_error' },
          ],
        },
        { status: 422 },
      ),
    );
    await expect(apiRequest('/auth/login')).rejects.toThrow(
      'password too long; not a valid email',
    );
  });

  it('falls back to a generic message when there is no detail, error, or status text', async () => {
    mockFetch.mockResolvedValue(new Response('not json', { status: 500, statusText: '' }));
    await expect(apiRequest('/ping')).rejects.toThrow('Request failed');
  });
});

describe('authApi.login', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch = mockFetch as typeof fetch;
    mockGetItem.mockReturnValue(null);
  });

  it('POSTs the credentials as JSON to /auth/login', async () => {
    mockFetch.mockResolvedValue(jsonResponse({ access_token: 'tok', token_type: 'bearer' }));
    await authApi.login('ada@example.com', 'hunter2');
    expect(lastCall()[0]).toBe(`${apiBaseUrl}/auth/login`);
    expect(lastCall()[1].method).toBe('POST');
    expect(lastCall()[1].body).toBe(
      JSON.stringify({ email: 'ada@example.com', password: 'hunter2' }),
    );
  });

  it('returns the access token and token type from the response', async () => {
    mockFetch.mockResolvedValue(jsonResponse({ access_token: 'tok', token_type: 'bearer' }));
    await expect(authApi.login('ada@example.com', 'hunter2')).resolves.toEqual({
      access_token: 'tok',
      token_type: 'bearer',
    });
  });
});

describe('authApi.checkUser', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch = mockFetch as typeof fetch;
    mockGetItem.mockReturnValue(null);
  });

  it('GETs the current user from /users/me', async () => {
    mockFetch.mockResolvedValue(jsonResponse(mockUser));
    await expect(authApi.checkUser()).resolves.toEqual(mockUser);
    expect(lastCall()[0]).toBe(`${apiBaseUrl}/users/me`);
    expect(lastCall()[1].method).toBeUndefined();
  });
});

describe('ApiError', () => {
  it('exposes the status and message it was constructed with', () => {
    const error = new ApiError(418, "I'm a teapot");
    expect(error).toBeInstanceOf(Error);
    expect(error.status).toBe(418);
    expect(error.message).toBe("I'm a teapot");
    expect(error.name).toBe('ApiError');
  });
});

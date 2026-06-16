import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Login, { clientAction } from '~/routes/auth/login';
import { ApiError, authApi } from '~/data/api';
import { safeSetItem } from '~/helpers/storage';
import { createRouteStub } from '../utils/createStub';

jest.mock('~/data/api', () => ({
  ...jest.requireActual('~/data/api'),
  authApi: { login: jest.fn() },
}));
jest.mock('~/helpers/storage');

const mockLogin = jest.mocked(authApi.login);
const mockSetItem = jest.mocked(safeSetItem);

function renderLogin(initialPath = '/login'): void {
  createRouteStub(
    [
      { path: '/login', Component: Login, action: clientAction },
      { path: '/', Component: () => <p>Home page</p> },
      { path: '/members', Component: () => <p>Members page</p> },
    ],
    { initialPath },
  );
}

async function fillAndSubmit(email: string, password: string): Promise<void> {
  const user = userEvent.setup();
  if (email) {
    await user.type(screen.getByLabelText(/email/i), email);
  }
  if (password) {
    await user.type(screen.getByLabelText(/password/i), password);
  }
  await user.click(screen.getByRole('button', { name: /sign in/i }));
}

describe('login route', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders the email and password fields and a submit button', () => {
    renderLogin();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('logs in with the entered credentials, stores the token, and redirects home', async () => {
    mockLogin.mockResolvedValue({ access_token: 'tok-123', token_type: 'bearer' });
    renderLogin();

    await fillAndSubmit('ada@example.com', 'hunter2');

    await waitFor(() => expect(screen.getByText('Home page')).toBeInTheDocument());
    expect(mockLogin).toHaveBeenCalledWith('ada@example.com', 'hunter2');
    expect(mockSetItem).toHaveBeenCalledWith('token', 'tok-123');
  });

  it('redirects to the redirect_url from the query string after login', async () => {
    mockLogin.mockResolvedValue({ access_token: 'tok-123', token_type: 'bearer' });
    renderLogin('/login?redirect_url=%2Fmembers');

    await fillAndSubmit('ada@example.com', 'hunter2');

    await waitFor(() => expect(screen.getByText('Members page')).toBeInTheDocument());
  });

  it('shows an error and stores no token when the credentials are invalid', async () => {
    mockLogin.mockRejectedValue(new ApiError(401, 'Unauthorized'));
    renderLogin();

    await fillAndSubmit('ada@example.com', 'wrong');

    expect(await screen.findByRole('alert')).toHaveTextContent(/invalid email or password/i);
    expect(mockSetItem).not.toHaveBeenCalled();
  });

  it('returns a validation error without calling the api when a field is empty', async () => {
    const formData = new FormData();
    formData.set('email', 'ada@example.com');
    formData.set('password', '');
    const request = new Request('http://localhost/login', { method: 'POST', body: formData });

    const result = await clientAction({ request } as Parameters<typeof clientAction>[0]);

    expect(result).toEqual({ error: 'Enter your email and password.' });
    expect(mockLogin).not.toHaveBeenCalled();
  });
});

import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ApiError, authApi } from '~/data/api';
import Signup, { clientAction, meta } from '~/routes/auth/signup';
import { createRouteStub } from '../utils/createStub';

jest.mock('~/data/api', () => ({
  ...jest.requireActual('~/data/api'),
  authApi: { signup: jest.fn() },
}));

const mockSignup = jest.mocked(authApi.signup);

function renderSignup(): void {
  createRouteStub(
    [
      { path: '/signup', Component: Signup, action: clientAction },
      { path: '/login', Component: () => <p>Login page</p> },
    ],
    { initialPath: '/signup' },
  );
}

async function fillAndSubmit({
  firstName = 'Ada',
  lastName = 'Lovelace',
  email = 'ada@example.com',
  phone = '07123456789',
  password = 'hunter22',
  confirmPassword = 'hunter22',
}: {
  firstName?: string;
  lastName?: string;
  email?: string;
  phone?: string;
  password?: string;
  confirmPassword?: string;
} = {}): Promise<void> {
  const user = userEvent.setup();
  if (firstName) await user.type(screen.getByLabelText(/first name/i), firstName);
  if (lastName) await user.type(screen.getByLabelText(/last name/i), lastName);
  if (email) await user.type(screen.getByLabelText(/email/i), email);
  if (phone) await user.type(screen.getByLabelText(/phone/i), phone);
  if (password) await user.type(screen.getByLabelText(/^password/i), password);
  if (confirmPassword) {
    await user.type(screen.getByLabelText(/confirm password/i, { selector: 'input' }), confirmPassword);
  }
  await user.click(screen.getByRole('button', { name: /create account/i }));
}

describe('signup route', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders the member signup form', () => {
    renderSignup();

    expect(screen.getByRole('heading', { name: /create your account/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/first name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/last name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/phone/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^password/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm password/i, { selector: 'input' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /show password/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /show confirm password/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument();
  });

  it('toggles password visibility with the eye buttons', async () => {
    const user = userEvent.setup();
    renderSignup();

    expect(screen.getByLabelText(/^password/i)).toHaveAttribute('type', 'password');
    await user.click(screen.getByRole('button', { name: /show password/i }));
    expect(screen.getByLabelText(/^password/i)).toHaveAttribute('type', 'text');
    expect(screen.getByRole('button', { name: /hide password/i })).toBeInTheDocument();

    expect(screen.getByLabelText(/confirm password/i, { selector: 'input' })).toHaveAttribute(
      'type',
      'password',
    );
    await user.click(screen.getByRole('button', { name: /show confirm password/i }));
    expect(screen.getByLabelText(/confirm password/i, { selector: 'input' })).toHaveAttribute(
      'type',
      'text',
    );
    expect(screen.getByRole('button', { name: /hide confirm password/i })).toBeInTheDocument();
  });

  it('creates a member account and redirects to login', async () => {
    mockSignup.mockResolvedValue({ id: 1, member_number: 'TTA-000001' });
    renderSignup();

    await fillAndSubmit();

    await waitFor(() => expect(screen.getByText('Login page')).toBeInTheDocument());
    expect(mockSignup).toHaveBeenCalledWith({
      first_name: 'Ada',
      last_name: 'Lovelace',
      email: 'ada@example.com',
      phone: '07123456789',
      password: 'hunter22',
    });
  });

  it('omits phone from the api payload when it is blank', async () => {
    mockSignup.mockResolvedValue({ id: 1, member_number: 'TTA-000001' });
    renderSignup();

    await fillAndSubmit({ phone: '' });

    await waitFor(() => expect(screen.getByText('Login page')).toBeInTheDocument());
    expect(mockSignup).toHaveBeenCalledWith({
      first_name: 'Ada',
      last_name: 'Lovelace',
      email: 'ada@example.com',
      password: 'hunter22',
    });
  });

  it('shows field errors after submit when required fields are missing', async () => {
    const user = userEvent.setup();
    renderSignup();

    await user.click(screen.getByRole('button', { name: /create account/i }));

    expect(screen.getByText('Enter your last name.')).toBeInTheDocument();
    expect(screen.getByText('Enter your email.')).toBeInTheDocument();
    expect(screen.getByText('Enter a password.')).toBeInTheDocument();
    expect(screen.getByText('Confirm your password.')).toBeInTheDocument();
    expect(mockSignup).not.toHaveBeenCalled();
  });

  it('clears a field error when the user types in that field', async () => {
    const user = userEvent.setup();
    renderSignup();

    await user.click(screen.getByRole('button', { name: /create account/i }));
    expect(screen.getByText('Enter your last name.')).toBeInTheDocument();

    await user.type(screen.getByLabelText(/last name/i), 'Lovelace');

    expect(screen.queryByText('Enter your last name.')).not.toBeInTheDocument();
    expect(screen.getByText('Enter your email.')).toBeInTheDocument();
  });

  it('shows a valid-email error after submit', async () => {
    const user = userEvent.setup();
    renderSignup();

    await user.type(screen.getByLabelText(/last name/i), 'Lovelace');
    await user.type(screen.getByLabelText(/email/i), 'ada');
    await user.type(screen.getByLabelText(/^password/i), 'hunter22');
    await user.type(screen.getByLabelText(/confirm password/i, { selector: 'input' }), 'hunter22');
    await user.click(screen.getByRole('button', { name: /create account/i }));

    expect(screen.getByText('Enter a valid email address.')).toBeInTheDocument();
    expect(mockSignup).not.toHaveBeenCalled();
  });

  it('shows a confirm-password error after submit when passwords do not match', async () => {
    const user = userEvent.setup();
    renderSignup();

    await user.type(screen.getByLabelText(/last name/i), 'Lovelace');
    await user.type(screen.getByLabelText(/email/i), 'ada@example.com');
    await user.type(screen.getByLabelText(/^password/i), 'hunter22');
    await user.type(screen.getByLabelText(/confirm password/i, { selector: 'input' }), 'different');
    await user.click(screen.getByRole('button', { name: /create account/i }));

    expect(screen.getByText('Passwords must match.')).toBeInTheDocument();
    expect(mockSignup).not.toHaveBeenCalled();
  });

  it('returns a validation error without calling the api when required fields are missing', async () => {
    const request = new Request('http://localhost/signup', {
      method: 'POST',
      body: new FormData(),
    });

    const result = await clientAction({ request } as Parameters<typeof clientAction>[0]);

    expect(result).toEqual({ error: 'Check the highlighted fields and try again.' });
    expect(mockSignup).not.toHaveBeenCalled();
  });

  it('returns a validation error when the password is too short', async () => {
    const formData = new FormData();
    formData.set('last_name', 'Lovelace');
    formData.set('email', 'ada@example.com');
    formData.set('password', 'short');
    formData.set('confirm_password', 'short');
    const request = new Request('http://localhost/signup', { method: 'POST', body: formData });

    const result = await clientAction({ request } as Parameters<typeof clientAction>[0]);

    expect(result).toEqual({ error: 'Check the highlighted fields and try again.' });
    expect(mockSignup).not.toHaveBeenCalled();
  });

  it('shows a duplicate-account message for 409 api errors', async () => {
    mockSignup.mockRejectedValue(new ApiError(409, 'A user with this email already exists'));
    renderSignup();

    await fillAndSubmit();

    expect(await screen.findByRole('alert')).toHaveTextContent(/account with this email/i);
  });

  it('shows the api error message for non-conflict ApiErrors', async () => {
    mockSignup.mockRejectedValue(new ApiError(422, 'password too short'));
    renderSignup();

    await fillAndSubmit();

    expect(await screen.findByRole('alert')).toHaveTextContent('password too short');
  });

  it('re-throws unexpected non-ApiError failures so they reach the ErrorBoundary', async () => {
    mockSignup.mockRejectedValue(new Error('network down'));
    const formData = new FormData();
    formData.set('first_name', 'Ada');
    formData.set('last_name', 'Lovelace');
    formData.set('email', 'ada@example.com');
    formData.set('password', 'hunter22');
    formData.set('confirm_password', 'hunter22');
    const request = new Request('http://localhost/signup', { method: 'POST', body: formData });

    await expect(clientAction({ request } as Parameters<typeof clientAction>[0])).rejects.toThrow(
      'network down',
    );
  });

  it('builds the page title from meta', () => {
    expect(meta()).toContainEqual({ title: 'Sign up | rosetta' });
  });
});

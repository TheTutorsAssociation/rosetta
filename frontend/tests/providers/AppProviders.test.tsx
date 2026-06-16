import { render, screen, waitFor } from '@testing-library/react';
import { createRoutesStub } from 'react-router';
import { AppProviders } from '~/providers/AppProviders';
import { useAuth } from '~/providers/AuthProvider';
import { useToast } from '~/providers/ToastProvider';
import { authApi } from '~/data/api';
import { safeGetItem } from '~/helpers/storage';
import { mockUser } from '../mocks';

jest.mock('~/data/api', () => ({
  authApi: { checkUser: jest.fn() },
}));
jest.mock('~/helpers/storage');

const mockCheckUser = jest.mocked(authApi.checkUser);
const mockGetItem = jest.mocked(safeGetItem);

function ContextProbe() {
  const { user } = useAuth();
  const { showToast } = useToast();
  return (
    <div>
      <span data-testid="user">{user ? user.name : 'none'}</span>
      <span data-testid="has-toast">{typeof showToast === 'function' ? 'yes' : 'no'}</span>
    </div>
  );
}

describe('AppProviders', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('makes both the auth and toast contexts available to children', async () => {
    mockGetItem.mockReturnValue('a-token');
    mockCheckUser.mockResolvedValue(mockUser);

    const Stub = createRoutesStub([
      {
        path: '*',
        Component: () => (
          <AppProviders>
            <ContextProbe />
          </AppProviders>
        ),
      },
    ]);
    render(<Stub initialEntries={['/']} />);

    await waitFor(() => expect(screen.getByTestId('user')).toHaveTextContent('Ada Lovelace'));
    expect(screen.getByTestId('has-toast')).toHaveTextContent('yes');
  });
});

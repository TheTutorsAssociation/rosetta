import { screen } from '@testing-library/react';
import Home from '~/routes/home';
import { createRouteStub } from '../utils/createStub';

function renderHome(): void {
  createRouteStub([{ path: '/', Component: Home }]);
}

describe('home route', () => {
  it('renders the rosetta wordmark heading', () => {
    renderHome();
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('rosetta');
  });

  it('links through to the sign-in page', () => {
    renderHome();
    expect(screen.getByRole('link', { name: /sign in/i })).toHaveAttribute('href', '/login');
  });
});

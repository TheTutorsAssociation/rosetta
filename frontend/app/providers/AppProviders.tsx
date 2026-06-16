import { type ReactNode } from 'react';
import { AuthProvider } from './AuthProvider';
import { ToastProvider } from './ToastProvider';

interface AppProvidersProps {
  children: ReactNode;
}

/**
 * Composition root for cross-cutting context providers, rendered once in
 * `root.tsx` around the route `<Outlet />`. Add providers here one concern at a
 * time, outermost first.
 *
 * `AuthProvider` is outermost: it validates the stored bearer token on load and
 * redirects unauthenticated traffic to `/login` (respecting the public routes).
 */
export function AppProviders({ children }: AppProvidersProps) {
  return (
    <AuthProvider>
      <ToastProvider>{children}</ToastProvider>
    </AuthProvider>
  );
}

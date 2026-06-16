import type { Route } from './+types/login';
import { useState } from 'react';
import { Form, redirect, useActionData, useNavigation, useSearchParams } from 'react-router';
import { Alert, Button, Heading, Input } from '~/components/ui';
import { ApiError, authApi } from '~/data/api';
import { buildMetaData } from '~/helpers/meta';
import { safeSetItem } from '~/helpers/storage';

export function meta(): Route.MetaDescriptors {
  return buildMetaData('Sign in');
}

type ActionResult = { error: string };

/**
 * Login action. Runs client-side only (`clientAction`) because it writes the
 * bearer token to `localStorage`, which the SSR server has no access to.
 * Validates the credentials, exchanges them for a token via `authApi.login`,
 * stores it, and redirects to the originally-attempted URL (or home). Invalid
 * credentials are returned to the form as an inline error; unexpected errors
 * bubble to the `ErrorBoundary`.
 */
export async function clientAction({
  request,
}: Route.ClientActionArgs): Promise<Response | ActionResult> {
  const formData = await request.formData();
  const email = String(formData.get('email') ?? '');
  const password = String(formData.get('password') ?? '');
  const redirectUrl = String(formData.get('redirect_url') ?? '');

  if (!email || !password) {
    return { error: 'Enter your email and password.' };
  }

  try {
    const { access_token } = await authApi.login(email, password);
    safeSetItem('token', access_token);
    return redirect(redirectUrl || '/');
  } catch (error) {
    if (error instanceof ApiError) {
      return { error: 'Invalid email or password.' };
    }
    throw error;
  }
}

export default function Login() {
  const actionData = useActionData<ActionResult>();
  const navigation = useNavigation();
  const [searchParams] = useSearchParams();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const redirectUrl = searchParams.get('redirect_url') ?? '';
  const isSubmitting = navigation.state === 'submitting';

  return (
    <main className="container-narrow flex min-h-[70vh] flex-col justify-center py-16">
      <div className="mx-auto w-full max-w-sm">
        <Heading level={1} className="font-serif text-primary">
          Sign in
        </Heading>
        <p className="mb-6 text-body text-neutral-700">
          Sign in to your Tutors&apos; Association account.
        </p>

        <Form method="post" className="space-y-5">
          {actionData?.error && <Alert variant="danger">{actionData.error}</Alert>}

          <input type="hidden" name="redirect_url" value={redirectUrl} />

          <Input
            name="email"
            type="email"
            label="Email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />

          <Input
            name="password"
            type="password"
            label="Password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />

          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Signing in…' : 'Sign in'}
          </Button>
        </Form>
      </div>
    </main>
  );
}

import type { Route } from './+types/home';
import { Button, Heading } from '~/components/ui';
import { APP_NAME, buildMetaData } from '~/helpers/meta';

export function meta(): Route.MetaDescriptors {
  return buildMetaData('Home');
}

/**
 * Index route. The rosetta landing screen: a deep-red serif wordmark, a short
 * subtitle, and a link into the sign-in flow.
 */
export default function Home() {
  return (
    <main className="container-narrow py-16">
      <Heading level={1} className="font-serif text-primary">
        {APP_NAME}
      </Heading>
      <p className="mb-8 max-w-prose text-body text-neutral-700">
        The membership platform for The Tutors&apos; Association.
      </p>
      <Button href="/login">Sign in</Button>
    </main>
  );
}

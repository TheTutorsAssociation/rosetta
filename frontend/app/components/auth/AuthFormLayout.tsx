import type { ReactNode } from 'react';
import { Heading } from '~/components/ui';

interface AuthFormLayoutProps {
  title: string;
  intro: string;
  children: ReactNode;
}

/** Shared centered auth form shell for login/signup routes. */
export function AuthFormLayout({ title, intro, children }: AuthFormLayoutProps) {
  return (
    <main className="container-narrow flex min-h-[70vh] flex-col justify-center py-16">
      <section className="card-surface mx-auto w-full max-w-md px-6 py-7">
        <Heading level={1} className="font-serif text-primary">
          {title}
        </Heading>
        <p className="mb-6 text-body text-neutral-700">{intro}</p>
        {children}
      </section>
    </main>
  );
}

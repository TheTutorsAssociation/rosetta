# Style Guide

Code conventions for the rosetta frontend. They are intentionally strict and enforced (ESLint
`--max-warnings 0` + Prettier + `tsc --strict`), so an agent or teammate can extend the
codebase without re-deriving taste. The matching test discipline is in
[`TESTING_GUIDE.md`](./TESTING_GUIDE.md). For patterns not present here (the full UI kit, list
screens, the icon factory), see the
[`tc-fullstack-starter`](https://github.com/tutorcruncher/tc-fullstack-starter) template.

## TypeScript

- **Strict mode, no `any`.** If a type is missing, define it (in `app/types/`) or narrow it —
  do not reach for `any` or a blanket cast. `unknown` + a narrowing check is fine.
- **Explicit return types on exported functions and components.** Components return
  `JSX.Element` (or `JSX.Element | null` when they can render nothing).
- **Props via explicit interfaces / type aliases. No wild HTML-attr spread.** Declare exactly the
  props a component accepts; do not `extends React.HTMLAttributes<...>` and `{...rest}` arbitrary
  attributes onto an element. If you need to forward a specific attribute (e.g. `aria-label`,
  `type`), name it on the props type.

  ```tsx
  // Good
  interface ButtonProps {
    children: React.ReactNode;
    variant?: ButtonVariant;
    onClick?: () => void;
    disabled?: boolean;
    type?: 'button' | 'submit';
  }
  export function Button({ children, variant = 'primary', ...handlers }: ButtonProps): JSX.Element {
    /* ... */
  }
  ```

  ```tsx
  // Avoid — opaque surface, unsafe attributes leak through
  export function Button(props: React.ButtonHTMLAttributes<HTMLButtonElement>) { /* ... */ }
  ```

- **Use generated route types.** In a route module, `import type { Route } from './+types/<route>'`
  and type the loader/action/component with `Route.LoaderArgs` / `Route.ActionArgs` /
  `Route.ComponentProps`. Never hand-type `params`. Run `npm run typecheck` (which runs
  `react-router typegen` first) after changing `routes.ts`.

## Styling — Tailwind v4

- **Design tokens live in the `@theme` block of `app/app.css`.** There is no `tailwind.config.js`.
  The token set is a generic semantic palette (`--color-primary-*`, `--color-secondary-*`,
  `--color-neutral-*`, `--color-success-*`, `--color-warning-*`, `--color-error-*`), spacing, and a
  text scale (`--text-display`, `--text-h1`, `--text-h2`, `--text-h3`, `--text-body`,
  `--text-small`). Reskin by editing this one block.
- **No inline styles, no `style` props.** Use Tailwind utilities only.
- **No arbitrary Tailwind values** (`w-[437px]`, `text-[#abc123]`, `mt-[13px]`). Use a token or a
  scale step. If a value genuinely doesn't exist in the scale, add it to `@theme` rather than
  inlining it once.
- **Use the semantic text scale**, not the framework defaults. Prefer `text-h2`, `text-body`,
  `text-small` over `text-xl`/`text-base`/`text-sm`, so a font/size change in `@theme` propagates
  everywhere.

## Class composition — the single `cn()` helper

There is exactly **one** way to compose class names: the `cn()` helper in `~/helpers/cn` (a thin
wrapper over `clsx`). No raw string concatenation, no `.trim()` cleanup, no template-string class
soup.

```tsx
import { cn } from '~/helpers/cn';

<div className={cn('rounded-lg border', isActive && 'border-primary-500', className)} />;
```

## Variant maps

Visual variants are declared as a `Record<Variant, string>` map and composed with `cn()`. This
keeps styling declarative and auditable, and is the pattern every `ui/` primitive follows
(`Alert` is the reference implementation).

```tsx
type AlertVariant = 'danger' | 'warning' | 'info' | 'success';

const VARIANT_CLASSES: Record<AlertVariant, string> = {
  danger: 'bg-error-soft border-error-soft text-error',
  warning: 'bg-warning-soft border-warning-soft text-warning',
  info: 'bg-info-soft border-info-soft text-info',
  success: 'bg-success-soft border-success-soft text-success',
};

export function Alert({ variant = 'danger', children, className }: AlertProps): JSX.Element {
  return <div role="alert" className={cn('rounded-md border px-4 py-3', VARIANT_CLASSES[variant], className)}>{children}</div>;
}
```

## Headings — use the `Heading` component

Do not write raw `<h1>`–`<h6>`. Use `Heading` from `~/components/ui`. It separates **visual size**
(`level`, 1–6, maps to a `text-*` token) from the **semantic tag** (`as`, defaults to the matching
`h{level}`). Pick the visual `level` first; only set `as` when the document outline requires a
different tag.

```tsx
<Heading level={1}>Sign in</Heading>          // <h1> at display size
<Heading level={2} as="h1">Page not found</Heading> // visually an h2, semantically the page <h1>
```

Exceptions: containers that render externally-styled HTML (e.g. a markdown/prose region) where the
downstream styling owns the tag.

## UI primitives

- **Check `app/components/ui/` before writing a new component.** The primitives that ship here are
  `Button`, `Input`, `Heading`, `Alert`, and `ErrorState`. Compose them before writing new ones;
  the broader kit (Table, Modal, Select, Pagination, SearchInput, Badge, Card, LoadingState) lives
  in the [`tc-fullstack-starter`](https://github.com/tutorcruncher/tc-fullstack-starter) template —
  port a primitive from there (with its test) when a screen needs it, rather than reinventing it.
- **Import from the barrel**: `import { Button, Heading } from '~/components/ui';`.
- **Accessibility is not optional.** Every interactive element has the right role/label and
  keyboard support (`Alert` uses `role="alert"`; `Input` wires `aria-invalid`/`aria-describedby`).

## Providers

- **One concern per provider**, composed in `app/providers/AppProviders.tsx`.
- **Each provider exposes a `use<Name>()` hook that throws when used outside its provider** (so a
  missing provider fails loudly at the call site rather than returning `undefined`).
- **Memoize the context value** (`useMemo`) and exposed handlers (`useCallback`) to avoid
  re-render cascades.

```tsx
const ToastContext = createContext<ToastContextValue | null>(null);

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within ToastProvider');
  return ctx;
}
```

## Config & storage access

- **`import.meta.env` is read only in `app/helpers/env.ts`.** Everything else imports the typed
  constants (`apiBaseUrl`, `sentryDsn`, `logfireTraceUrl`) from there. Optional integrations
  resolve to `undefined` when their env var is unset, so they self-disable with zero config.
- **`localStorage` is accessed only via `safeGetItem` / `safeSetItem` / `safeRemoveItem`** in
  `app/helpers/storage.ts` (SSR-safe, incognito-safe, quota-safe). Direct `localStorage` access is
  disallowed.

## Imports & path alias

- **`~/*` → `app/*`** for all cross-folder imports (`import { cn } from '~/helpers/cn'`). Use it
  everywhere except sibling/`./` relative imports within the same folder. The alias resolves
  identically in build, dev, and tests.

## Formatting

Prettier owns formatting: single quotes, semicolons, `trailingComma: all`, `printWidth: 100`,
`tabWidth: 2`. Run `npm run format`; pre-commit applies it via lint-staged. Don't hand-fight it.

# CLAUDE.md — rosetta frontend

Context for AI coding agents (and humans) working in this folder. This is the **production
frontend** for The Tutors' Association membership platform. It is deliberately minimal: only
code that is actually used ships here, and everything that ships is tested (100% coverage gate).

This was scaffolded from the
[`tc-fullstack-starter`](https://github.com/tutorcruncher/tc-fullstack-starter) template. For
the full pattern library — the example resource, the complete UI kit (Table, Modal, Select,
Pagination, SearchInput, Badge, Card, LoadingState), the data hooks (`useOrderParams`,
`useAsyncAction`, `useClickOutside`), date/pagination helpers, and the list/detail/form
worked example — read that template rather than reinventing them here.

Code conventions are in [`STYLE_GUIDE.md`](./STYLE_GUIDE.md); test discipline in
[`TESTING_GUIDE.md`](./TESTING_GUIDE.md); architecture in [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md);
customization knobs in [`docs/CUSTOMIZATION.md`](./docs/CUSTOMIZATION.md).

## Stack

- **React Router v7** (framework mode, SSR on by default — `react-router.config.ts` sets `ssr: true`).
- **React 19** + **TypeScript 5.8** (strict).
- **Tailwind CSS v4** — design tokens in the `@theme` block of `app/app.css`; no `tailwind.config.js`.
- **Vite 6** (plugins: `@tailwindcss/vite`, `@react-router/dev/vite`, `vite-tsconfig-paths`).
- **Jest 30** + ts-jest + Testing Library; **Playwright** for e2e.
- **ESLint 9** flat config + Prettier + Husky + lint-staged.
- **npm** only. Node 20 LTS (`.nvmrc`).

## What's here

```
app/
├── components/
│   └── ui/          # Primitives: Button, Input, Heading, Alert, ErrorState
├── data/
│   └── api.ts       # Single typed HTTP client: apiRequest<T>, ApiError, authApi
├── helpers/         # cn, env, meta, monitoring, routes, storage
├── providers/       # AppProviders, AuthProvider, ToastProvider
├── routes/
│   ├── home.tsx     # / landing
│   ├── not-found.tsx# * catch-all
│   └── auth/login.tsx # /login (clientAction)
├── app.css          # Tailwind v4 entry + @theme tokens
├── prose.css        # Optional generic markdown styling
├── root.tsx         # Layout + App + ErrorBoundary + links
├── entry.client.tsx # hydrateRoot(HydratedRouter) in StrictMode
└── routes.ts        # Programmatic route manifest
tests/
├── utils/           # renderWithRouter / renderWithProviders / createRouteStub
├── mocks/           # Typed mock data (mockUser)
├── components/ helpers/ providers/ routes/   # mirror app/
e2e/                 # Playwright specs + auth.setup.ts + fixtures/auth.ts
docs/                # ARCHITECTURE.md, CUSTOMIZATION.md
```

The auth flow: `AuthProvider` reads the bearer token from storage on the client, validates it
via `authApi.checkUser()` (`GET /users/me`), and redirects unauthenticated traffic to `/login`
(preserving the attempted URL) on non-public routes. `/login`'s `clientAction` exchanges
credentials for a token, stores it via the `safe*` storage wrappers, and redirects.

## Common commands

```bash
npm ci             # install (CI, Husky, Docker all use npm ci)
npm run dev        # dev server (http://localhost:5001)
npm run typecheck  # react-router typegen && tsc — run after route changes
npm run lint       # eslint, --max-warnings 0
npm run lint:fix   # eslint --fix
npm run format     # prettier --write
npm test           # jest + coverage (gate: 100% statements/branches/functions/lines)
npm run test:watch # jest --watch
npm run test:e2e   # playwright test
npm run build      # production build
npm run start      # serve the production build
```

Pre-commit (Husky) runs `typecheck → test → lint-staged`. Keep all of them green.

## Conventions

These are the rules every change is held to. The "why" for each is in `STYLE_GUIDE.md` /
`TESTING_GUIDE.md`.

- **SSR is on. Load data in route `loader`s and mutate in route `action`s** through the single
  typed `app/data/api.ts` client. **Never call `fetch()` directly in a component.** All HTTP goes
  through `apiRequest<T>`, which throws `ApiError(status, message)` on failure — loaders let it
  bubble to the `ErrorBoundary`; actions catch it and return an inline error to the form.
- **Drive list state (page, search, sort) from the URL** via `useSearchParams`; the loader reads
  the search params. Never hold list/filter state in component `useState`. (No list screens exist
  yet — follow the template when you add one.)
- **Use generated route types**: `import type { Route } from './+types/<route>'` and type
  loaders/actions/components with `Route.LoaderArgs` / `Route.ActionArgs` / `Route.ComponentProps`.
  Run `npm run typecheck` after route changes.
- **Style with variant maps** (`Record<Variant, string>`) composed via the single `cn()` helper
  (`~/helpers/cn`). No inline styles, no `style` props, no arbitrary Tailwind values.
- **Tailwind v4 tokens live in the `@theme` block of `app/app.css`** (semantic colors, spacing,
  and a text scale `text-display`/`text-h1..h3`/`text-body`/`text-small`). There is no
  `tailwind.config.js`.
- **Use the `Heading` component** (`level` for visual size, `as` for the semantic tag) instead of
  raw `<h1>`–`<h6>`. **Use the `ui/` primitives before writing new ones**; import from the barrel
  `~/components/ui`.
- **Every interactive element** has an ARIA role/label and keyboard support.
- **Compose cross-cutting state in `AppProviders`; one concern per provider.** Expose a `use<Name>()`
  hook that **throws when used outside its provider**. Memoize context values (`useMemo`) and
  handlers (`useCallback`).
- **Access `import.meta.env` only in `app/helpers/env.ts`**; access `localStorage` only via the
  `safe*` wrappers in `app/helpers/storage.ts`. Optional integrations (Sentry/Logfire) self-disable
  when their env var is unset.
- **Path alias `~/*` → `app/*`** for all cross-folder imports (kept in sync across `tsconfig`,
  `vite-tsconfig-paths`, and the jest `moduleNameMapper`).
- **Tests:** one reason per test. Query priority `getByRole` > `getByLabelText` >
  `getByPlaceholderText` > `getByText` > `getByTestId`. No snapshots. Render via the shared helpers
  (`renderWithRouter` / `renderWithProviders`); **mock the api layer, not internal logic.** Route
  loader/action tests use `createRouteStub` with a mocked api. **100% coverage** is enforced; the
  framework shell (`root.tsx`, `entry.client.tsx`, `routes.ts`, `**/+types/**`) is excluded.

## Customize / extend

To add a real resource (types, api object, route tree, list/detail/form, tables, pagination,
URL-driven state, an e2e spec), copy the worked example from the
[`tc-fullstack-starter`](https://github.com/tutorcruncher/tc-fullstack-starter) template by
analogy. The starting points to edit here:

1. **`app/data/api.ts`** — add resource objects (mirror the `list`/`get`/`create`/`update`/`remove`
   shape) alongside `authApi`.
2. **`app/routes.ts`** + `app/routes/` — register your resource tree.
3. **`app/app.css` `@theme` tokens** — the one place to reskin (colors, text scale, spacing).
4. **`app/types/`** — add resource types; re-export from `index.ts`.

See [`docs/CUSTOMIZATION.md`](./docs/CUSTOMIZATION.md) for the full recipe.

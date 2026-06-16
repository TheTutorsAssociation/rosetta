# rosetta — frontend

The web frontend for **The Tutors' Association** membership platform, built with
**React Router v7** (framework mode, SSR on) + **React 19** + **TypeScript** (strict) +
**Tailwind CSS v4** + **Vite**.

This is a deliberately **minimal, honest** codebase: only the production code that is actually
used ships here, and everything that ships is covered by tests (100% coverage gate). For the
full pattern library this was scaffolded from — the example resource, the complete UI kit,
list/table/pagination/form patterns, the data hooks — see the
[`tc-fullstack-starter`](https://github.com/tutorcruncher/tc-fullstack-starter) template.

## What's here

- **Routes:** `/login` (sign-in form + `clientAction`), `/` (landing), and a `*` not-found.
- **Providers:** `AuthProvider` (validates the stored token via `GET /users/me`, redirects
  unauthenticated traffic to `/login`), `ToastProvider`, composed in `AppProviders`.
- **UI primitives** (`app/components/ui/`): `Button`, `Input`, `Heading`, `Alert`, `ErrorState`.
- **Typed API client** (`app/data/api.ts`): `apiRequest<T>`, `ApiError`, `authApi`.
- **Helpers** (`app/helpers/`): `cn`, `env`, `meta`, `monitoring`, `routes`, `storage`.

## Stack

| Concern | Choice |
| --- | --- |
| Framework | React Router v7 (framework/SSR mode) |
| UI runtime | React 19 |
| Language | TypeScript 5.8 (strict) |
| Styling | Tailwind CSS v4 (`@theme` tokens, no `tailwind.config.js`) |
| Build / dev | Vite 6 |
| Data | RR7 route loaders + actions through one typed `app/data/api.ts` |
| Unit / component tests | Jest 30 + ts-jest + Testing Library |
| E2E tests | Playwright |
| Lint / format | ESLint 9 (flat config) + Prettier + Husky + lint-staged |
| Package manager | npm (only) |
| Node | 20 LTS (pinned in `.nvmrc`) |

## Quick start

```bash
npm ci                       # install from the committed package-lock.json
cp .env.example .env         # set VITE_API_BASE_URL (defaults to the backend on http://localhost:5000)
npm run dev                  # dev server on http://localhost:5001
```

Verify the toolchain end to end:

```bash
npm run typecheck            # react-router typegen && tsc (strict, no errors)
npm run lint                 # eslint, --max-warnings 0
npm test                     # jest + coverage gate (100% statements/branches/functions/lines)
npm run build                # production build into build/
npm run start                # serve the production build
```

All of the above must pass clean on a fresh clone.

## Project structure

```
app/
├── components/
│   └── ui/          # Primitives: Button, Input, Heading, Alert, ErrorState
├── data/            # api.ts — the single typed HTTP client
├── helpers/         # cn, env, meta, monitoring, routes, storage
├── providers/       # AppProviders, AuthProvider, ToastProvider
├── routes/          # home, not-found, auth/login
├── app.css          # Tailwind v4 entry + @theme design tokens
├── prose.css        # Optional generic markdown styling
├── root.tsx         # RR7 root: Layout, App, ErrorBoundary, links
├── entry.client.tsx # Client hydration entry
└── routes.ts        # Programmatic route manifest
tests/               # Jest tests mirroring app/ + shared render helpers + typed mocks
e2e/                 # Playwright specs + auth storage-state fixture
docs/                # ARCHITECTURE.md, CUSTOMIZATION.md
```

## Data flow

Data is loaded the idiomatic RR7 way: route **loaders** read the request and call the typed
`app/data/api.ts` client; route **actions** handle mutations. Components never call `fetch()`
directly. Failed requests throw `ApiError`, which either bubbles to the route `ErrorBoundary`
or is caught by an action and returned to the form as field errors. The `/login` route is the
worked example (a client-side `clientAction` that exchanges credentials for a token, stores it,
and redirects). See [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md).

To build out new resources (list/detail/form, tables, pagination, URL-driven state), follow the
[`tc-fullstack-starter`](https://github.com/tutorcruncher/tc-fullstack-starter) template — it
ships the full worked example and the primitives those screens need.

## Deployment

The primary deployment artifact is the **Dockerfile** (multi-stage `node:20-alpine`, builds
with `npm ci` + `npm run build`, runs `npm run start`):

```bash
docker build -t rosetta-frontend .
docker run -p 3000:3000 --env-file .env rosetta-frontend
```

A `Procfile` (`web: npm run start`) is included as an optional convenience for PaaS hosts that
read one; the Dockerfile is the source of truth.

## Optional monitoring

Monitoring is **not** a default dependency. `app/helpers/monitoring.ts` exposes a
`reportError(error)` that no-ops (logs to the console in dev) until you wire a vendor.
`app/helpers/env.ts` already surfaces `sentryDsn` and `logfireTraceUrl` (both `undefined`
when their env vars are unset, so integrations self-disable). To enable Sentry or Logfire,
follow [`docs/CUSTOMIZATION.md`](./docs/CUSTOMIZATION.md).

## Docs index

- [`CLAUDE.md`](./CLAUDE.md) — agent entry point: stack, structure, commands, conventions.
- [`STYLE_GUIDE.md`](./STYLE_GUIDE.md) — code conventions (TS, Tailwind tokens, primitives).
- [`TESTING_GUIDE.md`](./TESTING_GUIDE.md) — testing discipline + the 100% coverage gate.
- [`NOT_CARRIED_FORWARD.md`](./NOT_CARRIED_FORWARD.md) — what was trimmed and where the full
  pattern library lives.
- [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) — how SSR boots and data flows.
- [`docs/CUSTOMIZATION.md`](./docs/CUSTOMIZATION.md) — knobs (alias, providers, tokens, env,
  monitoring) and the pointer to the template for absent patterns.

# Architecture

How the rosetta frontend boots, renders, and moves data. It is a standard **React Router v7
framework-mode** app with SSR on — this doc explains the pieces so you can reason about (and
extend) the data flow without surprises. The patterns shown for list/detail/form screens are
not yet present here; port them from the
[`tc-fullstack-starter`](https://github.com/tutorcruncher/tc-fullstack-starter) template when you
add a resource.

## The big picture

```
request ──> server (SSR)              hydration ──> client
   │           │                          │
   │   matches routes.ts                  │   entry.client.tsx
   │   runs matched loaders               │   hydrateRoot(<HydratedRouter/>)
   │   renders root Layout + Outlet        │   loaders/actions now run via fetch
   │   streams HTML                        │   to the server route handlers
```

Both the server and the client run the **same route modules**. Loaders run on the server for the
initial request (real SSR), then on the client for subsequent client-side navigations.

## SSR boot & hydration

- **`react-router.config.ts`** — `export default { ssr: true } satisfies Config`. This is the
  single switch that puts the app in SSR mode. (Flipping it to `ssr: false` turns the app into a
  client-rendered SPA — see [`CUSTOMIZATION.md`](./CUSTOMIZATION.md).)
- **`app/root.tsx`** — the required RR7 root module. It exports:
  - **`Layout({ children })`** — wraps the *entire HTML document*:
    `<html><head><Meta/><Links/></head><body>{children}<ScrollRestoration/><Scripts/></body></html>`.
    This is essential for SSR: `<Meta/>`/`<Links/>` inject per-route metadata and stylesheets,
    `<Scripts/>` ships the client bundle, `<ScrollRestoration/>` restores scroll on navigation.
  - **`App()`** (default export) — renders `<Outlet/>` wrapped in `<AppProviders>`, so every route
    sits inside the app's cross-cutting context (Toast, and whatever else you compose in).
  - **`ErrorBoundary({ error })`** — catches errors from any route. It distinguishes
    `isRouteErrorResponse(error)` (404s and thrown route responses) from generic thrown `Error`s and
    renders the `ErrorState` primitive accordingly. It reports to monitoring only if monitoring is
    configured (via `reportError` — a no-op until you wire a vendor).
  - **`links`** — the `Route.LinksFunction` that includes `app.css`.
- **`app/entry.client.tsx`** — the client hydration entry. It calls
  `startTransition(() => hydrateRoot(document, <StrictMode><HydratedRouter /></StrictMode>))`. Note
  it uses **`HydratedRouter`**, not `BrowserRouter` — it re-attaches React to the server-rendered
  DOM rather than re-rendering from scratch. A commented block shows where optional monitoring
  (e.g. `Sentry.init`, gated on `import.meta.env.VITE_SENTRY_DSN`) hooks in *before* hydration.
- **`app/entry.server.tsx`** is **not customized** in this template — RR7 provides the default
  server entry, and the `isbot` dependency lets it decide between streaming and buffered rendering
  for bots vs browsers. Add an `app/entry.server.tsx` only if you need to customize that.

## Route matching — `app/routes.ts`

Routes are declared programmatically using the `@react-router/dev/routes` DSL (`index`, `route`,
`layout`, `prefix`), not by file-system convention. This makes the route tree explicit and easy for
an agent to extend. The current manifest is minimal:

```ts
import { type RouteConfig, index, route } from '@react-router/dev/routes';

export default [
  index('routes/home.tsx'),                 // /
  route('login', 'routes/auth/login.tsx'),  // /login
  route('*', 'routes/not-found.tsx'),       // catch-all 404
] satisfies RouteConfig;
```

When you add a resource, follow the file convention from the
[`tc-fullstack-starter`](https://github.com/tutorcruncher/tc-fullstack-starter) template:
`<resource>/<resource>.tsx` (list), `<resource>-layout.tsx` (a parent that loads the shared record
once and exposes it to its children via **`Outlet` context**, so detail and edit don't each
re-fetch), `<resource>-detail.tsx`, `<resource>-new.tsx`, `<resource>-edit.tsx`.

## Generated `+types` — type-safe routes

`react-router typegen` reads `routes.ts` and generates a `+types/<route>.d.ts` file next to each
route module (under `.react-router/types`, surfaced via the `rootDirs` setting in `tsconfig.json`).
Each route imports its own generated types:

```tsx
import type { Route } from './+types/login';

export async function clientAction({ request }: Route.ClientActionArgs) { /* request is typed */ }
export function meta(): Route.MetaDescriptors { return buildMetaData('Sign in'); }
export default function Login() { /* … */ }
```

This keeps `params`, `loaderData`, and `meta` type-safe and **breaks the build when the route tree
changes**. `npm run typecheck` runs typegen first, so always run it after editing `routes.ts`.

## Data flow — loaders, actions, and `app/data/api.ts`

All data movement goes through **one typed HTTP client**, `app/data/api.ts`. Components and routes
never call `fetch()` directly.

```
loader/action ──> authApi.login()/checkUser()/… ──> apiRequest<T>(path, opts)
                                                      │
                                          base URL + JSON headers (+ optional token)
                                                      │
                                              fetch ──> response
                                                      │
                              ok? parse JSON : throw ApiError(status, message)
```

- **`apiRequest<T>(path, options?)`** — prepends `apiBaseUrl` (from `helpers/env.ts`), sets JSON
  headers (and an optional bearer token from `safeGetItem`), parses the JSON response, and on
  `!response.ok` throws **`ApiError`** with `status` and a message extracted from
  `json.detail ?? json.error ?? response.statusText`.
- **Resource objects** group a resource's endpoints. The one that ships is **`authApi`**
  (`login(email, password)` → `LoginResponse`, `checkUser()` → `User`). When you add a CRUD
  resource, mirror the `list(params?) / get(id) / create(payload) / update(id, payload) /
  remove(id)` shape from the
  [`tc-fullstack-starter`](https://github.com/tutorcruncher/tc-fullstack-starter) template, with
  typed returns.
- **`PaginatedResponse<T> = { items: T[]; total: number; page: number; page_size: number }`** is the
  standard list-envelope type, ready for when you add a list endpoint (`page_size` snake_case
  mirrors a typical backend).

### Worked example — the `/login` route

`app/routes/auth/login.tsx` is the data-flow reference in this codebase. It uses a **`clientAction`**
(client-only, because it writes the bearer token to `localStorage`, which the SSR server can't
reach): it validates the credentials, exchanges them via `authApi.login`, stores the token with
`safeSetItem`, and `redirect`s to the originally-attempted URL (or `/`). Invalid credentials are
**caught and returned to the form** as an inline error; unexpected errors are **re-thrown** to the
`ErrorBoundary`:

```tsx
export async function clientAction({ request }: Route.ClientActionArgs) {
  const form = await request.formData();
  const email = String(form.get('email') ?? '');
  const password = String(form.get('password') ?? '');
  if (!email || !password) return { error: 'Enter your email and password.' };
  try {
    const { access_token } = await authApi.login(email, password);
    safeSetItem('token', access_token);
    return redirect(String(form.get('redirect_url') ?? '') || '/');
  } catch (error) {
    if (error instanceof ApiError) return { error: 'Invalid email or password.' };
    throw error; // unexpected → ErrorBoundary
  }
}
```

### List routes & mutations

List loaders read **URL search params** (page, search, sort) — not component state — and call the
resource's `list`, so back/forward, sharing, and reload all work. Create/edit/delete go through
route **actions** that call `create`/`update`/`remove`, then `redirect` on success or catch
`ApiError` and return field errors. These screens don't exist here yet; the full worked loader,
URL-driven table, and action examples live in the
[`tc-fullstack-starter`](https://github.com/tutorcruncher/tc-fullstack-starter) template.

### Error propagation

- In a **loader**, let `ApiError` bubble — RR7 routes it to the nearest `ErrorBoundary` (the root
  one renders `ErrorState`).
- In an **action**, catch `ApiError` and return it as data so the form can show an `Alert`; re-throw
  anything unexpected so it still reaches the `ErrorBoundary`.
- Success/failure user feedback (toasts) is fired client-side via `useToast` from the route
  component after the action resolves.

## Styling pipeline

`app/app.css` is the Tailwind v4 entry (`@import 'tailwindcss'`). Design tokens are declared in its
`@theme` block (there is no `tailwind.config.js`); `@layer base` styles native form controls,
`@layer components` defines reusable utility classes, `@layer utilities` holds keyframes and
animation helpers (e.g. the toast entry animation). Tailwind compiles via the `@tailwindcss/vite`
plugin (first in the Vite plugin order). `prose.css` is an optional generic markdown stylesheet
imported from `app.css`.

## Vite plugin order

`vite.config.ts` registers three plugins **in this order**:
`tailwindcss()` → `reactRouter()` → `tsconfigPaths()`. Tailwind first so styles compile; the RR7
plugin provides SSR + typegen + the route build; `vite-tsconfig-paths` makes the `~/*` alias resolve
in dev and build (mirrored by `tsconfig` paths and the jest `moduleNameMapper`).

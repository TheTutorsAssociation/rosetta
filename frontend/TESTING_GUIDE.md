# Testing Guide

How tests are written and run in the rosetta frontend. The goal is a small, self-documenting
suite that exercises the real React Router data flow without a backend, mocks only the API
boundary, and holds a **100% coverage gate** on everything that ships. Code conventions are in
[`STYLE_GUIDE.md`](./STYLE_GUIDE.md). For test patterns covering screens not present here (list
loaders, table/form/pagination tests, the e2e walkthrough), see the
[`tc-fullstack-starter`](https://github.com/tutorcruncher/tc-fullstack-starter) template.

## Goals

- **One reason per test.** Each test covers a distinct behavior or branch; its name states what.
  No "just in case" tests, no two tests covering the same thing.
- **Mock only the boundary.** Mock `app/data/api.ts` (the HTTP layer) — never internal business
  logic, hooks, or components under test.
- **Test through the user's eyes.** Query the way a user (and assistive tech) would: by role and
  label, not by implementation detail.
- **Keep tests complete but lean.** Cover every code path (happy, error, loading, empty, each
  branch) with the fewest tests that do so. Share setup via `beforeEach` and the shared helpers.

## Tooling

- **Jest 30 + ts-jest** (config in `jest.config.cjs`), **jsdom** environment.
- **Testing Library** (`@testing-library/react`, `@testing-library/jest-dom`,
  `@testing-library/user-event`) for component/route tests.
- **Playwright** for e2e (`e2e/`, config in `playwright.config.ts`).

```bash
npm test             # run all tests with coverage (CI gate)
npm run test:watch   # watch mode
npm test -- <path>   # a single file
npm run test:e2e     # playwright
```

## Test layout

Tests mirror `app/`:

```
tests/
├── utils/
│   ├── render.tsx       # renderWithRouter / renderWithProviders
│   └── createStub.tsx   # createRouteStub (loader/action route tests)
├── mocks/
│   ├── index.ts         # re-exports all mock data
│   └── users.ts         # mockUser
├── components/          # component unit tests (mirror app/components)
├── helpers/             # helper-function tests
├── providers/           # provider/context tests
└── routes/              # route loader/action tests
```

## Query priority

Always reach for the most accessible query first. Drop to the next only when the one above can't
express the intent:

1. `getByRole` — accessible roles (`button`, `textbox`, `link`, `dialog`, …) + the `name` option.
2. `getByLabelText` — form fields by their visible label.
3. `getByPlaceholderText` — inputs identified by placeholder.
4. `getByText` — visible text content.
5. `getByTestId` — last resort, with an explicit `data-testid`.

Use `query*` for absence assertions, `find*` for async appearance.

## No snapshots, no comments

- **No snapshot tests.** They assert too much, churn on every change, and document nothing.
  Assert the specific thing the test is about.
- **No comments in test files** (other than nothing — tests should be self-documenting). The
  `describe`/`it` names and the code structure carry the intent. If a test needs a comment to be
  understood, rename it or split it.

## Typed data factories

Build test data from the typed mocks in `tests/mocks/`, never inline ad-hoc objects scattered
across files. A mock is a fully-typed object; a factory takes overrides and returns one:

```ts
import type { User } from '~/types';

export const mockUser: User = {
  id: 1,
  name: 'Ada Lovelace',
  email: 'ada@example.com',
};
```

Re-export everything from `tests/mocks/index.ts` so tests import from one place. When you add a
resource, add a `build<Resource>s(count, overrides)` factory alongside its mock (see the
[`tc-fullstack-starter`](https://github.com/tutorcruncher/tc-fullstack-starter) template for the
pattern).

## Render helpers

There is **one** authoritative render path — never call Testing Library's bare `render` with an
ad-hoc router wrapper in individual tests.

- **`renderWithRouter(ui, options?)`** — wraps `ui` in a RR7 router (memory/`createRoutesStub`).
  Use for components that use `<Link>`, `useNavigate`, etc., but no provider context.
- **`renderWithProviders(ui, options?)`** — additionally wraps in `AppProviders` (so `useToast`
  and friends resolve). Use for components that consume cross-cutting context.

```tsx
import { renderWithProviders } from '~/../tests/utils/render';

renderWithProviders(<SomeComponent />);
```

## Loader/action route tests — `createRouteStub`

To test a route's **loader/action data flow** in isolation, mock the api layer and drive the route
through `createRouteStub` (a thin wrapper over React Router's `createRoutesStub`). This runs the
real loader/action against the mocked api and renders the route exactly as RR7 would — no backend.
The `/login` route is the worked example in this codebase (`tests/routes/login.test.tsx`):

```tsx
import Login, { clientAction } from '~/routes/auth/login';
import { authApi } from '~/data/api';
import { createRouteStub } from '~/../tests/utils/createStub';

jest.mock('~/data/api', () => ({
  ...jest.requireActual('~/data/api'),
  authApi: { login: jest.fn() },
}));
const mockLogin = jest.mocked(authApi.login);

it('logs in and redirects on success', async () => {
  mockLogin.mockResolvedValue({ access_token: 'tok', token_type: 'bearer' });

  createRouteStub(
    [
      { path: '/login', Component: Login, action: clientAction },
      { path: '/', Component: () => <p>Home page</p> },
    ],
    { initialPath: '/login' },
  );
  // …fill the form and submit, then assert the redirect
});
```

Common api-mock shapes:

```ts
mockApi.method.mockResolvedValue(result);                  // success → render / redirect
mockApi.method.mockRejectedValue(new ApiError(500, 'Server error')); // error → ErrorBoundary or Alert
```

## What to cover

For each component/route/helper, ensure tests cover:

- Happy path (normal render/operation).
- Error states (api rejects → `ErrorBoundary` or form `Alert`).
- Loading/pending UI where applicable.
- Empty states (no rows → empty message).
- Each conditional branch (every `if`/`else`, each variant).
- User interactions (clicks, typing, form submit, sort toggle, pagination).

Group related assertions about a single behavior into one test; keep success vs failure paths,
and behaviors with different setup, separate.

## End-to-end (Playwright)

- **Sequential**: `workers: 1` to avoid login rate limits and per-test re-login.
- **Auth via storage state**: a one-time `e2e/auth.setup.ts` project logs in once and saves the
  storage state; the `chromium` project depends on `setup` and reuses it. Specs import `{ test, expect }`
  from `e2e/fixtures/auth.ts`, which exposes an `authedPage` fixture built on that saved state. Add
  more roles by extending the fixture, not by re-logging-in per test.
- **Server**: started by Playwright in CI (`webServer.command: 'npm run dev'`), reused locally
  (`reuseExistingServer: !process.env.CI`). `baseURL` comes from `E2E_BASE_URL`.
- The `e2e/` setup (`auth.setup.ts` + `fixtures/auth.ts`) provides the authenticated fixture; add
  feature specs against it. The full worked e2e walkthrough (list → new → form → detail → edit)
  lives in the [`tc-fullstack-starter`](https://github.com/tutorcruncher/tc-fullstack-starter)
  template.

## Coverage gates

Committed thresholds (enforced in CI by `npm test`):

| Metric | Threshold |
| --- | --- |
| Statements | 100% |
| Branches | 100% |
| Functions | 100% |
| Lines | 100% |

The framework shell is **excluded** from coverage because it is untestable glue, not logic:
`app/root.tsx`, `app/entry.client.tsx`, `app/routes.ts`, and any `**/+types/**`. If you add a new
piece of pure framework wiring, add it to `coveragePathIgnorePatterns` in `jest.config.cjs` and
note why. Everything else must be covered — prefer a real test for every branch (including error
paths); only when a line is genuinely unreachable in jsdom, exclude it narrowly with
`/* istanbul ignore next */` plus a one-line justification.

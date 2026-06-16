# rosetta — agent guide

rosetta is a **full-stack monorepo** with two independent apps. Its conventions and best-practices
follow TutorCruncher's [`tc-fullstack-starter`](https://github.com/tutorcruncher/tc-fullstack-starter)
template — refer to the template for the full pattern library (pagination, list filters, the read-only
public API, multi-tenancy, etc.). **rosetta itself contains only production code that is actually in use.**

There is no shared toolchain — work **within one folder at a time** and follow **that folder's**
`CLAUDE.md`, which is the authoritative guide for its stack:

- **[`backend/`](backend/CLAUDE.md)** — FastAPI · SQLModel · Celery. Python 3.12, `uv`, `ruff`, `ty`,
  `pytest`. Postgres + Redis. Run commands from `backend/` (`make …`, `uv run …`).
- **[`frontend/`](frontend/CLAUDE.md)** — React Router v7 (SSR) · React 19 · Tailwind v4 · Vite.
  TypeScript, `npm`, `eslint`, `prettier`, `jest`, Playwright. Run commands from `frontend/` (`npm …`).

## Rules for working here

1. **Stay in one stack.** Don't run `uv`/`pytest`/`ruff` outside `backend/`, or `npm`/`jest`/`eslint`
   outside `frontend/`. Each folder has its own lockfile, config, and CLAUDE.md.
2. **Follow the folder's CLAUDE.md and `.claude/rules/`** for all conventions (they are detailed and
   stack-specific). This root file only routes you.
3. **For anything that spans both halves** — login/auth, calling the API, CORS, the request/response
   contract (error format, field casing), SSR data loading — read
   **[`INTEGRATION.md`](INTEGRATION.md)** first and keep both sides consistent.
4. **CI is path-scoped** (`.github/workflows/backend.yml`, `frontend.yml`, `frontend-e2e.yml`): a change
   under `backend/**` runs backend CI, a change under `frontend/**` runs frontend CI. Keep the gates
   green for the half you touched (backend: 100% patch coverage; frontend: 80/75/70/75).

## What's here

- **Backend:** auth (`POST /auth/login`, `GET /users/me`), role/permission checks, Celery wired for the
  upcoming Mailchimp task, and `scripts/seed.py`. New features copy the template's patterns — see
  `backend/CLAUDE.md` and the tc-fullstack-starter template.
- **Frontend:** React Router v7 SSR app — see `frontend/CLAUDE.md`.
- **Both:** keep the base URL and auth aligned per `INTEGRATION.md`.

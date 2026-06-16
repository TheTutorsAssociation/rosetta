# rosetta backend

A **FastAPI + SQLModel + Celery + PostgreSQL** backend for the TTA membership platform.

Conventions and best-practices follow TutorCruncher's
[`tc-fullstack-starter`](https://github.com/tutorcruncher/tc-fullstack-starter) template — refer
to the template for the full pattern library (pagination, list filters, the read-only public
API, multi-tenancy, the example-domain slice). **This repo carries only production code that is
actually in use**; the conventions are documented in [`CLAUDE.md`](./CLAUDE.md) and meant to be
followed exactly.

## What's here

- **Auth** — `POST /auth/login` issues a JWT; `auth_user` validates it and sets
  `request.state.user`. `GET /users/me` returns the current user.
- **User types** — `UserType` (`ADMIN` / `MEMBER` / `CONTACT`, on the `user_type` field) + an
  orthogonal `is_superadmin` flag, enforced with composable `Permission` route dependencies.
- **Celery** — wired (worker + task registration) for the upcoming Mailchimp member sync.
- **Core** — config, the `DBSession` access layer, Redis, Logfire + Sentry, Alembic migrations,
  and an idempotent `scripts/seed.py` superadmin seed.
- **Tests** mirroring the app structure, using factories, full-structure assertions, and role
  clients, at 100% patch coverage.

## Stack

| Layer | Choice |
|-------|--------|
| Web framework | FastAPI (`fastapi[standard]`) |
| ORM / models | SQLModel (SQLAlchemy + Pydantic) |
| Database | PostgreSQL |
| Migrations | Alembic (config under `[tool.alembic]` in `pyproject.toml`) |
| Background tasks | Celery with a Redis broker |
| Auth | Web Bearer JWT (PyJWT) + argon2 password hashing (`pwdlib`) |
| Observability | Logfire + Sentry |
| Tooling | `uv`, `ruff` (lint + format), `ty` (type-check), `pytest` (+ `pytest-xdist`, `factory-boy`) |
| Python | 3.12+ |

## Quickstart

### 1. Prerequisites

- Python 3.12+
- [`uv`](https://github.com/astral-sh/uv)
- A running PostgreSQL and Redis (locally, or via Docker):

```bash
docker run -d --name starter-postgres -e POSTGRES_HOST_AUTH_METHOD=trust -p 5432:5432 postgres:16
docker run -d --name starter-redis -p 6379:6379 redis:7
```

### 2. Install dependencies

```bash
make install-dev      # uv sync --dev + pre-commit install
```

### 3. Configure the environment

```bash
cp .env.example .env
```

Edit `.env` to point at your Postgres/Redis and set a real `SECRET_KEY` for non-dev runs
(the app refuses to boot in non-dev/test mode while the insecure default secret is in place).

### 4. Apply migrations and seed

```bash
uv run alembic upgrade head
make seed             # idempotent superadmin
```

### 5. Run the app and the worker

```bash
make run-dev          # uvicorn app.main:app --reload   (http://localhost:5000)
make run-worker       # celery -A app.worker worker -l info
```

- API docs (Scalar): `http://localhost:5000/scalar`
- Healthcheck: `GET http://localhost:5000/`

### 6. Run the checks

```bash
make test             # uv run pytest -n auto
make test-cov         # with coverage, fails under 98%
make lint             # ruff check + ruff format --check + ty check
```

CI gates patch coverage at 100% (via `diff-cover`) and uploads coverage to Codecov under the
`backend` flag (token `CODECOV_TOKEN`).

## Adding a feature

1. Read [`CLAUDE.md`](./CLAUDE.md) and the relevant files under `.claude/rules/`.
2. Copy the matching pattern from the `tc-fullstack-starter` template for each layer you add:
   model (`_Base`/`Table`/`Basic`) → schemas → `api/` router → optional `tasks.py` → tests.
3. Wire new model modules into `app/__init__.py` so `SQLModel.metadata` is complete, and
   include new routers in `app/main.py`.
4. Generate a migration (`uv run alembic revision --autogenerate -m '...'`), verify a single
   head, and apply it.
5. Run `make lint` and `make test-cov` (100% patch coverage on new code).
6. Self-check against [`PR_REVIEW_PATTERNS.md`](./PR_REVIEW_PATTERNS.md) before opening a PR.

## Deployment & the "migrations run on deploy" model

This project assumes **migrations run on deploy**: the deploy pipeline runs
`alembic upgrade head` before the new application code starts serving, so application code can
always assume the database schema is up to date.

Consequences for the code you write:

- **Do not** add fallback code for "old" database states.
- **Do not** add runtime checks for whether a column/table exists.
- If a migration adds a column with a non-null default, assume every row has that value.

> **Dual schema path (intentional):** tests build the schema with `create_test_schema`
> (`SQLModel.metadata.create_all`) for speed and isolation, while production and CI use
> Alembic. CI applying `alembic upgrade head` keeps the two paths from drifting.

## Where to go next

- [`CLAUDE.md`](./CLAUDE.md) — conventions and the rules-reference table.
- [`STYLE_GUIDE.md`](./STYLE_GUIDE.md) — consolidated code style.
- [`PR_REVIEW_PATTERNS.md`](./PR_REVIEW_PATTERNS.md) — ranked pre-PR self-review checklist.
- `.claude/rules/` — category-grouped rules with examples.
- [`tc-fullstack-starter`](https://github.com/tutorcruncher/tc-fullstack-starter) — the full
  pattern library for anything not yet present in rosetta.
```

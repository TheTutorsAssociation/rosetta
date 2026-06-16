# rosetta backend — development guide for AI agents

FastAPI · SQLModel · Celery · PostgreSQL · Redis. Python 3.12, `uv`, `ruff`, `ty`, `pytest`.

rosetta's conventions and best-practices follow TutorCruncher's
[`tc-fullstack-starter`](https://github.com/tutorcruncher/tc-fullstack-starter) template.
**Refer to the template for the full pattern library** — pagination, list filters/ordering, the
read-only public API (`/api/v1`, per-org API keys), multi-tenancy / `request_query`
org-scoping, the example-domain vertical slice. **rosetta itself contains only production code
that is actually in use**, so this guide documents only what's here. When you add a feature,
generalize the template's pattern for that layer rather than inventing a new one.

## What's actually here

- **Auth** — `POST /auth/login` (`app/auth/api/login.py`) issues a JWT; `auth_user`
  (`app/auth/jwt.py`) validates it and sets `request.state.user`. `GET /users/me`
  (`app/auth/api/users.py`) returns `request.state.user` directly.
- **Roles & permissions** — `UserRole` (`ADMIN` / `MEMBER`) plus an `is_superadmin` flag, and
  composable `Permission` dependencies (`is_admin` / `is_member` / `is_superadmin` / `everyone`
  / `anonymous`) in `app/auth/permissions.py`. Apply them as route/router `dependencies=[...]`,
  never as handler-body checks.
- **Model layer** — `User` / `UserBasic` (`app/auth/models.py`) on the thin `AppModel`
  (`app/common/models.py`) SQLModel base. Field factories `UTCDatetimeField` / `EnumField` live
  in `app/common/fields.py`.
- **Errors** — the `HTTP400…HTTP500` classes in `app/common/api/errors.py`. Raise these, never
  `HTTPException` directly.
- **Rate limiting** — `rate_limit_by_ip` (`app/common/api/rate_limit.py`) on the login route.
- **Celery** — `app/core/celery.py` + `app/worker.py`, wired for the upcoming Mailchimp sync
  task. Run with `make run-worker`.
- **Core** — config (`app/core/config.py`), the `DBSession` access layer
  (`app/core/database.py`), redis, logging, Sentry, Alembic migrations, and `scripts/seed.py`
  (idempotent superadmin seed).

## House rules

1. **`url_path_for` / `request.url_for` for every URL**, in app code and tests — never hardcode
   a path. Routes get descriptive kebab-case `name=`s (`login`, `users-me`).
2. **Schema split — `_Base` / `Table` / `Basic`.** Define a non-table `_Model(AppModel)` base
   with shared columns, a `Model(_Model, table=True)` that adds `id` + secrets + relationships,
   and a `ModelBasic(_Model)` that adds `id` but omits secrets. Set `response_model=ModelBasic`
   and return the ORM row — secrets (`hashed_password`) that live only on the table class then
   physically cannot leak. `User` / `UserBasic` is the live example.
3. **Module-level imports only.** No function-level imports (except a `TYPE_CHECKING` block or a
   strictly-necessary circular-import break). **Never** add `from __future__ import annotations`.
4. **Type hints everywhere**, prefer `X | None` over `Optional[X]`, single quotes, 120-col
   lines. `make lint` (ruff check + format-check + ty) must pass. Use ty's native ignore codes
   (`# ty: ignore[unresolved-attribute]`), never mypy-style; narrow DB ids with
   `assert obj.id is not None`.
5. **Tests** — `uv run pytest -n auto` (always `-n auto`). Use factories (`create_with_db`),
   `db.create()`, never explicit ids. Name response vars `r`. Assert the **complete** response
   structure. Use `auth_client` by default; role clients only for permission boundaries. No
   comments except a top-of-function docstring. **98% overall coverage, 100% patch coverage** —
   every new branch (including error paths) needs a test; mock the specific call if a branch
   isn't reachable through normal setup.
6. **Migrations run on deploy.** Assume the schema is current; no fallback code for "old" DB
   states. One migration per PR; verify a single head (`alembic heads`). New flags default to
   `False` (opt-in).
7. **DBSession helpers** — `db.create`, `db.get_or_404`, `db.exists`, `db.get_or_create`,
   `db.create_or_update` (the last already commits). Use `get_session()` in Celery tasks,
   `get_db()` in routes.

## Common commands

```bash
make run-dev        # uvicorn app.main:app --reload
make run-worker     # celery -A app.worker worker -l info
make lint           # ruff check + ruff format --check + ty check
make type-check     # ty check .
make test           # uv run pytest -n auto
make test-cov       # with coverage, fails under 98%
make seed           # idempotent superadmin seed
uv run alembic upgrade head
```

## Detailed rules

Category-grouped rules with examples live in `.claude/rules/`:

| Category | Files |
|----------|-------|
| **API** | `api/error-handling.md`, `api/responses.md`, `api/rate-limiting.md` |
| **Code Style** | `code-style/documentation.md`, `code-style/imports.md` |
| **Database** | `database/session.md`, `database/security.md` |
| **Tasks** | `tasks/celery.md` |
| **Testing** | `testing/url-generation.md`, `testing/data-creation.md`, `testing/assertions.md`, `testing/client-usage.md`, `testing/style.md` |
| **Tooling** | `tooling/typing.md` |

Top-level docs: `STYLE_GUIDE.md` (consolidated code style) and `PR_REVIEW_PATTERNS.md`
(pre-PR self-review checklist). For any pattern not present in rosetta yet, the
`tc-fullstack-starter` template is the reference.

## Project structure

```
backend/
├── app/
│   ├── auth/                 # login, jwt, permissions, User model
│   ├── common/               # AppModel base, field factories, api/{errors,rate_limit}
│   ├── core/                 # config, database, celery, redis, logging, sentry
│   ├── main.py               # FastAPI app
│   └── worker.py             # Celery worker entry point
├── migrations/               # Alembic env + versions/
├── scripts/seed.py           # idempotent superadmin seed
├── tests/                    # mirrors app/ (+ conftest, base_factory)
└── .claude/rules/            # detailed, category-grouped rules
```

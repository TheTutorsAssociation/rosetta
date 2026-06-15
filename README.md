# rosetta

The **The Tutors' Association (TTA)** membership platform — a bespoke replacement for Wild Apricot.

A **FastAPI + SQLModel + Celery** backend (`backend/`) and a **React Router v7** frontend (`frontend/`),
built on TutorCruncher's [`tc-fullstack-starter`](https://github.com/tutorcruncher/tc-fullstack-starter)
conventions. Single-tenant (TTA only). The first version covers the **staff admin** side (members,
payments, events, reporting) **and the member login area / hub**; the public marketing website and the
public "Find a Tutor" directory come later.

> **Status:** scaffolding. The build is tracked in [issues](../../issues) — start at the
> [M1 Members & onboarding epic](../../issues/4).

## 📄 Documents — what to read and why

### Project briefs (start here)
| Document | What it is | Who it's for |
|---|---|---|
| **[OVERVIEW.md](OVERVIEW.md)** | Plain-English feature brief — every feature and **what it will / won't do (yet)**, what's deferred and why. | TTA staff (Julius, Myra, Sam) & the board — **read this to approve scope.** |
| **[BRIEF.md](BRIEF.md)** | Technical build brief — architecture, data model, scope with requirement-ID traceability, and where we diverge from the Nucleus RFP. | Developers. |

### How the codebase is built (conventions — follow exactly)
| Document | Covers |
|---|---|
| **[CLAUDE.md](CLAUDE.md)** | Root agent guide — routes you to the right stack folder. |
| **[INTEGRATION.md](INTEGRATION.md)** | How backend ↔ frontend talk: auth/JWT, CORS, the API request/response contract, SSR. Read before any full-stack change. |
| **[backend/CLAUDE.md](backend/CLAUDE.md)** | Backend conventions entry point (FastAPI · SQLModel · Celery). |
| **[backend/README.md](backend/README.md)** | Backend setup, commands, and the "add a domain slice" workflow. |
| **[backend/STYLE_GUIDE.md](backend/STYLE_GUIDE.md)** | Backend code style. |
| **[backend/PR_REVIEW_PATTERNS.md](backend/PR_REVIEW_PATTERNS.md)** | Pre-PR self-review checklist (mined from real review comments). |
| **[backend/.claude/rules/](backend/.claude/rules/)** | Detailed rules: api, code-style, database, tasks, testing, tooling. |
| **[frontend/CLAUDE.md](frontend/CLAUDE.md)** | Frontend conventions entry point (React Router v7 · React 19 · Tailwind v4). |
| **[frontend/README.md](frontend/README.md)** | Frontend setup, commands, and the "add a resource" workflow. |
| **[frontend/STYLE_GUIDE.md](frontend/STYLE_GUIDE.md)** | Frontend code style. |
| **[frontend/TESTING_GUIDE.md](frontend/TESTING_GUIDE.md)** | Frontend testing discipline (Jest + Playwright). |
| **[frontend/docs/ARCHITECTURE.md](frontend/docs/ARCHITECTURE.md)** | Data flow, SSR boot, loaders/actions. |
| **[frontend/docs/CUSTOMIZATION.md](frontend/docs/CUSTOMIZATION.md)** | How to wire auth, env vars, providers, theming. |
| **[frontend/NOT_CARRIED_FORWARD.md](frontend/NOT_CARRIED_FORWARD.md)** | What the starter template intentionally left out. |

> The backend and frontend are **independent** — work in one folder at a time and follow *that folder's*
> `CLAUDE.md`. The root files above only route you and cover the contract between the two.

## Stack & layout

| | Backend (`backend/`) | Frontend (`frontend/`) |
|---|---|---|
| Stack | FastAPI · SQLModel · Celery · Postgres · Redis | React Router v7 (SSR) · React 19 · Tailwind v4 · Vite |
| Tooling | Python 3.12 · `uv` · `ruff` · `ty` · `pytest` | TypeScript · `npm` · ESLint · Prettier · Jest · Playwright |
| Dev server | `:8000` | `:5173` |
| Tests | `pytest` — 100% patch coverage | Jest — 80/75/70/75 + Playwright e2e |

## Quick start

```bash
# Backend (needs local Postgres + Redis) — http://localhost:8000
cd backend && make install-dev && uv run alembic upgrade head && make run-dev

# Frontend — http://localhost:5173 (talks to the backend on :8000)
cd frontend && npm ci && cp .env.example .env && npm run dev
```

See each folder's `README.md` for the full per-stack quick start.

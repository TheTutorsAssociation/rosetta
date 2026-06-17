---
paths:
  - "app/**/models/*.py"
  - "app/**/models.py"
  - "app/**/api/*.py"
---

# Index the fields a list view filters and sorts on

**Every column a list endpoint filters or sorts on must have an index the query can actually
use.** Without one, the database falls back to a sequential scan: fine on 10 rows in a test,
slow on 50,000 in production. Add the index when you add the filter/sort — not after it's slow.

The index has to match the query shape — the wrong kind helps nothing:

| Query on the column | Index to add |
|---|---|
| **Sort** (`ORDER BY`, incl. the paginate-then-fetch page query) | B-tree (`index=True`). Always — `ORDER BY` + `LIMIT/OFFSET` need it for stable, fast paging. |
| **Equality / FK filter** (`status == …`, `company_id == …`) | B-tree (`index=True`; `FKField` already indexes). |
| **Range filter** (dates, numbers: `created_dt >= …`) | B-tree. |
| **Substring / `ILIKE` search** (`col.ilike('%term%')`) | A **`pg_trgm` GIN index** — a B-tree can't serve a leading-wildcard `%term%`, so `index=True` does nothing here. `pg_trgm` is already enabled (see `conftest`). |

**Skip the index when it can't help.** A plain B-tree on a very low-cardinality column (a
boolean, a two-value enum like `verification_status`) is rarely used by the planner and just
costs writes — leave it off, or fold the column into a **composite** index when it's a hot
filter that always precedes a sort (e.g. a list always filtered by `company_id` then ordered by
`created_dt` → one `(company_id, created_dt)` index serves both).

## How to declare them

- **B-tree** — on the model `Field`: `Field(index=True)`, `UTCDatetimeField(..., index=True)`;
  `FKField` indexes its column automatically. `User.email` / `Member.member_number` /
  `Member.created_dt` are live examples.
- **Trigram (for `ILIKE` search)** — not expressible on a SQLModel `Field`; add it in the Alembic
  migration:
  ```python
  op.create_index(
      'ix_member_search_trgm', 'member', ['member_number'],
      postgresql_using='gin', postgresql_ops={'member_number': 'gin_trgm_ops'},
  )
  ```
  (and the equivalent on the joined `User` name/email columns the search hits).

## Verify

The `count_queries` no-N+1 test proves the query *count* is constant — it does **not** prove the
queries use indexes. For a list on a table expected to grow, sanity-check the plan: `EXPLAIN` the
filtered/sorted query and confirm there's no `Seq Scan` on the filtered/sorted columns. When you
add a new filter or `ListOrder` field, add the matching index in the same PR.

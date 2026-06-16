---
paths:
  - "app/**/*.py"
---

# Database Security Patterns

## Secret fields live only on the table class

Use the `_Base` / `Table` / `Basic` model split so secrets (`hashed_password`, `hashed_key`)
are declared **only** on the `table=True` class. A `Basic` response schema then physically
cannot serialize them, even if a handler returns the ORM row directly. `User` /
`UserBasic` in `app/auth/models.py` is the live example — `hashed_password` lives only on
`User`.

## Query scoping and LIKE-injection (template patterns)

rosetta has no list/search endpoints yet, so it carries no `request_query` /
`query_for_pub_api` access-control scaffolding and no `escape_like` helper. When you add a
list or search endpoint, follow the `tc-fullstack-starter` template:

- scope every list/detail query through `Model.request_query(...)` (internal) or
  `Model.query_for_pub_api(...)` (public) — never replicate filters inline; and
- escape user input in `LIKE`/`ilike` queries (`escape_like`) so `%`/`_` can't act as
  wildcards and leak rows.

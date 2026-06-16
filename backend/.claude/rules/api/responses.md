---
paths:
  - "app/**/api/*.py"
---

# API URL and Response Patterns

Always use `url_path_for` for URL references. Declare a `response_model` on every endpoint and
return the ORM row directly.

## URL Generation with url_path_for

**ALWAYS use `url_path_for` instead of hardcoded URL paths.** This keeps URLs correct when routes change.

```python
from starlette.requests import Request

@router.get('/some-route')
def some_route(request: Request):
    other_url = request.url_for('other-route-name')
    return {'redirect_url': other_url}
```

### Route Naming Convention

Use descriptive kebab-case names (the live routes are `name='login'` and `name='users-me'`):

```python
@router.get('/users/me', name='users-me')
@anon_router.post('/login', name='login')
```

### Benefits

- **Type Safety**: FastAPI catches missing route names at startup
- **Maintainability**: Route changes only need to be updated in one place
- **Consistency**: All URLs follow the same pattern

## response_model + return the ORM row

Declare `response_model` on every endpoint and return the raw ORM instance. FastAPI
serializes it to the declared schema — no hand-mapping, and fields the schema omits never
leak. This pairs with the `_Base` / `Table` / `Basic` model split: secrets
(`hashed_password`, internal ids) live **only** on the table class, so a `Basic` schema
physically cannot expose them.

### ✅ Good — the live `/users/me` route

```python
@router.get('/me', response_model=UserBasic, name='users-me')
def get_current_user(request: Request) -> UserBasic:
    return UserBasic.model_validate(request.state.user, from_attributes=True)
```

### ❌ Bad - hand-mapping fields into a dict

```python
return {'id': user.id, 'email': user.email, 'user_type': user.user_type}
```

## List endpoints (template pattern)

rosetta has no list endpoints yet. When you add one, follow the `tc-fullstack-starter`
template's `PaginatedResponse[T]` shape (`items` / `total` / `page` / `page_size`) and its
paginate-then-fetch convention so per-page latency stays constant.

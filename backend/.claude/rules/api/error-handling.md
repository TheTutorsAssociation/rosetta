---
paths:
  - "app/**/*.py"
---

# API Error Handling

Use the custom HTTP error classes from `app.common.api.errors` and truncate error logs.

## HTTP Error Classes

Import from `app.common.api.errors`, NOT from `fastapi`:

```python
from app.common.api.errors import HTTP400, HTTP401, HTTP403, HTTP404

@router.get('/example-resources/{resource_id}', name='example-resource-detail')
def get_resource(resource_id: int, db: DBSession = Depends(get_db)):
    return db.get_or_404(ExampleResource, id=resource_id)
```

Available classes: `HTTP400`, `HTTP401`, `HTTP402`, `HTTP403`, `HTTP404`, `HTTP409`, `HTTP422`, `HTTP429`, `HTTP500`.

## Common Status Codes

| Code | Usage |
|------|-------|
| 200 | Success (GET, PUT, PATCH) |
| 201 | Created (POST) |
| 204 | No Content (DELETE) |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (not authenticated) |
| 402 | Payment Required (inactive billing) |
| 403 | Forbidden (not authorized) |
| 404 | Not Found |
| 409 | Conflict (duplicate) |
| 422 | Unprocessable Entity (Pydantic validation) |
| 429 | Too Many Requests (rate limited) |
| 500 | Internal Server Error |

## Use 404, Not 403, to Avoid Leaking Existence

When a lookup should be invisible to the caller (a resource they're not allowed to see),
raise `HTTP404`, not `HTTP403` — a 403 leaks that the resource exists. Scope the lookup and
raise `HTTP404` on a miss so not-found and not-allowed collapse into one branch. The
`tc-fullstack-starter` template shows the full multi-tenant version
(`request_query` + `HTTP404`); rosetta is single-tenant and has no cross-org resources yet.

## Error Logging

When logging API response bodies, truncate to prevent log bloat:

### ✅ Good - Truncated response
```python
logger.error('API call failed: %s %s', r.status_code, r.text[:1000])
```

### ❌ Bad - Unbounded response
```python
logger.error('API call failed: %s %s', r.status_code, r.text)
```

## Sanitize Public Error Responses

Public endpoints (especially health checks) must not leak internal details. Never put raw
exception messages, hostnames, connection strings, or stack traces into a response body.
Log the full detail internally and return a generic message.

### ✅ Good
```python
except Exception as e:
    logger.error('Health check failed: %s', e)
    raise HTTP500('Service health check failed')
```

## Error Response Format

FastAPI returns a consistent structure:

```python
{'detail': 'Human-readable error message'}
```

For validation errors (422):

```python
{'detail': [{'loc': ['body', 'field_name'], 'msg': 'field required', 'type': 'value_error.missing'}]}
```

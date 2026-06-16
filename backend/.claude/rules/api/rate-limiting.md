---
paths:
  - "app/**/api/*.py"
  - "app/common/api/rate_limit.py"
---

# Rate Limiting

The Redis-backed rate-limit dependency lives in `app/common/api/rate_limit.py`. rosetta keeps
the one helper it uses — `rate_limit_by_ip` — for throttling the anonymous login route. The
`tc-fullstack-starter` template carries the wider set (per-user `rate_limit` /
`confirm_rate_limit`, per-org `public_api_rate_limit`); pull them back from there if a feature
needs them.

## Per-IP, count-every-attempt — `rate_limit_by_ip`

For anonymous endpoints, throttle even failed attempts so credential stuffing is bounded.
`INCR` + an idempotent `EXPIRE ... NX` make the counter atomic and crash-safe (a worker
crash between INCR and EXPIRE can't leave a TTL-less, permanently-throttling key).

```python
@anon_router.post('/auth/login', name='login', dependencies=[Depends(rate_limit_by_ip('login', 60, 5))])
def login(credentials: UserLogin, session: DBSession = Depends(get_db)) -> Token:
    ...
```

`get_client_ip(request)` reads the **rightmost** `X-Forwarded-For` entry, which is only safe
behind a trusted proxy that appends the real client IP. Without such a proxy, an attacker can
spoof XFF — gate it on a trusted-proxy allowlist before relying on it for security.

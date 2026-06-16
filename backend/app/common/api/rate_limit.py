"""Redis-based rate limiting dependencies for FastAPI routes."""

from fastapi import Request

from app.common.api.errors import HTTP429
from app.core.redis import get_redis_client


def get_client_ip(request: Request) -> str:
    """Return the originating client IP from the proxy chain.

    **ONLY SAFE BEHIND A TRUSTED PROXY THAT APPENDS THE REAL CLIENT IP.** This function trusts
    the rightmost ``X-Forwarded-For`` entry unconditionally. That is correct behind a load
    balancer / router that always appends the real client IP, but on any deployment where the
    request can reach the app *without* such a proxy (local dev, a bare VM/pod with no ALB), an
    attacker can spoof ``X-Forwarded-For`` to bypass IP-keyed rate limits. If your topology does
    not guarantee a trusted proxy, gate this behind a ``trusted_proxy`` allowlist before relying
    on the result for security decisions.

    A trusted proxy appends the real client IP as the rightmost ``X-Forwarded-For`` entry (the
    existing list may have been set by the client and is untrustworthy), so we take the rightmost.
    Without this, IP-keyed rate limiting collapses to a single global bucket (the proxy IP from
    ``request.client.host``).
    """
    xff = request.headers.get('x-forwarded-for')
    if xff:
        rightmost = xff.rsplit(',', 1)[-1].strip()
        if rightmost:
            return rightmost
    return request.client.host if request.client else 'unknown'


def rate_limit_by_ip(prefix: str, window_seconds: int, max_attempts: int):
    """N attempts per IP per window. Uses INCR + idempotent EXPIRE for atomic counting.

    Every attempt is counted. Use this for anonymous auth endpoints where you want to throttle
    even failed attempts to defeat credential stuffing / brute force.

    The TTL is set with ``NX`` on every call (idempotent, no-op once set) so a worker crash
    between INCR and EXPIRE can't leave a TTL-less key permanently throttling that IP.

    Args:
        prefix: Key prefix to namespace different rate limits.
        window_seconds: Length of the window in seconds.
        max_attempts: Maximum attempts permitted per IP per window.

    Returns:
        A FastAPI dependency callable.
    """

    def _rate_limit_by_ip(request: Request) -> None:
        ip = get_client_ip(request)
        key = f'rate_limit:{prefix}:{ip}'
        redis_client = get_redis_client()
        count = redis_client.incr(key)
        redis_client.expire(key, window_seconds, nx=True)
        if count > max_attempts:
            raise HTTP429('Too many attempts. Please try again later.')

    return _rate_limit_by_ip

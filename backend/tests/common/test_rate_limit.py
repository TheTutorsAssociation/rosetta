import pytest
from starlette.requests import Request

from app.common.api.errors import HTTP429
from app.common.api.rate_limit import get_client_ip, rate_limit_by_ip
from app.core.redis import get_redis_client


def _build_request(headers: list[tuple[bytes, bytes]] | None = None, client: tuple[str, int] | None = None) -> Request:
    """Build a minimal Starlette request with optional headers and client address."""
    scope = {
        'type': 'http',
        'method': 'GET',
        'headers': headers or [],
        'path': '/',
        'query_string': b'',
    }
    if client is not None:
        scope['client'] = client
    return Request(scope)


class TestGetClientIp:
    """Tests for resolving the originating client IP from the proxy chain."""

    def test_uses_rightmost_x_forwarded_for_entry(self):
        """Test that the rightmost X-Forwarded-For entry is trusted over earlier ones."""
        request = _build_request(headers=[(b'x-forwarded-for', b'1.1.1.1, 2.2.2.2, 3.3.3.3')])

        assert get_client_ip(request) == '3.3.3.3'

    def test_single_x_forwarded_for_entry(self):
        """Test that a single X-Forwarded-For entry is returned as-is."""
        request = _build_request(headers=[(b'x-forwarded-for', b'9.9.9.9')])

        assert get_client_ip(request) == '9.9.9.9'

    def test_blank_x_forwarded_for_falls_back_to_client_host(self):
        """Test that a blank X-Forwarded-For value falls back to request.client.host."""
        request = _build_request(headers=[(b'x-forwarded-for', b'   ')], client=('5.5.5.5', 1234))

        assert get_client_ip(request) == '5.5.5.5'

    def test_no_header_uses_client_host(self):
        """Test that the client host is used when no X-Forwarded-For header is present."""
        request = _build_request(client=('4.4.4.4', 4321))

        assert get_client_ip(request) == '4.4.4.4'

    def test_no_header_and_no_client_returns_unknown(self):
        """Test that 'unknown' is returned when there is neither a header nor a client."""
        request = _build_request()

        assert get_client_ip(request) == 'unknown'


class TestRateLimitByIp:
    """Tests for the per-IP atomic counter dependency."""

    def test_allows_attempts_up_to_max(self):
        """Test that attempts up to max_attempts pass without raising."""
        get_redis_client().delete('rate_limit:login:7.7.7.7')
        dependency = rate_limit_by_ip('login', window_seconds=60, max_attempts=3)
        request = _build_request(client=('7.7.7.7', 1000))

        for _ in range(3):
            dependency(request)

    def test_blocks_attempt_over_max(self):
        """Test that the attempt after max_attempts raises HTTP429."""
        get_redis_client().delete('rate_limit:login:8.8.8.8')
        dependency = rate_limit_by_ip('login', window_seconds=60, max_attempts=2)
        request = _build_request(client=('8.8.8.8', 1000))

        dependency(request)
        dependency(request)
        with pytest.raises(HTTP429) as exc_info:
            dependency(request)

        assert exc_info.value.detail == 'Too many attempts. Please try again later.'

    def test_counter_is_scoped_per_ip(self):
        """Test that one IP exhausting its attempts does not throttle a different IP."""
        get_redis_client().delete('rate_limit:login:1.2.3.4')
        get_redis_client().delete('rate_limit:login:5.6.7.8')
        dependency = rate_limit_by_ip('login', window_seconds=60, max_attempts=1)

        dependency(_build_request(headers=[(b'x-forwarded-for', b'1.2.3.4')]))
        with pytest.raises(HTTP429):
            dependency(_build_request(headers=[(b'x-forwarded-for', b'1.2.3.4')]))

        dependency(_build_request(headers=[(b'x-forwarded-for', b'5.6.7.8')]))

    def test_sets_window_ttl_on_the_counter(self):
        """Test that the window ttl is applied to the per-IP counter key."""
        get_redis_client().delete('rate_limit:login:9.0.9.0')
        dependency = rate_limit_by_ip('login', window_seconds=45, max_attempts=5)

        dependency(_build_request(headers=[(b'x-forwarded-for', b'9.0.9.0')]))

        assert get_redis_client().ttl('rate_limit:login:9.0.9.0') == 45

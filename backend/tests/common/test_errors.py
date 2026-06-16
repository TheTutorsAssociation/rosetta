from app.common.api.errors import (
    HTTP400,
    HTTP401,
    HTTP402,
    HTTP403,
    HTTP404,
    HTTP409,
    HTTP422,
    HTTP429,
    HTTP500,
)


class TestHTTPErrors:
    def test_http400_initialization(self):
        """Test HTTP400 sets a 400 status, the detail, and supports headers."""
        error = HTTP400('Bad request')
        assert error.status_code == 400
        assert error.detail == 'Bad request'
        assert error.headers is None

        error_with_headers = HTTP400('Bad request', headers={'X-Custom': 'value'})
        assert error_with_headers.headers == {'X-Custom': 'value'}

    def test_http401_initialization(self):
        """Test HTTP401 sets a 401 status, the detail, and supports headers."""
        error = HTTP401('Unauthorized')
        assert error.status_code == 401
        assert error.detail == 'Unauthorized'
        assert error.headers is None

        error_with_headers = HTTP401('Unauthorized', headers={'WWW-Authenticate': 'Bearer'})
        assert error_with_headers.headers == {'WWW-Authenticate': 'Bearer'}

    def test_http402_initialization(self):
        """Test HTTP402 sets a 402 status, the detail, and supports headers."""
        error = HTTP402('Payment required')
        assert error.status_code == 402
        assert error.detail == 'Payment required'
        assert error.headers is None

        error_with_headers = HTTP402('Payment required', headers={'X-Custom': 'value'})
        assert error_with_headers.headers == {'X-Custom': 'value'}

    def test_http403_initialization(self):
        """Test HTTP403 sets a 403 status, the detail, and supports headers."""
        error = HTTP403('Forbidden')
        assert error.status_code == 403
        assert error.detail == 'Forbidden'
        assert error.headers is None

        error_with_headers = HTTP403('Forbidden', headers={'X-Custom': 'value'})
        assert error_with_headers.headers == {'X-Custom': 'value'}

    def test_http404_initialization(self):
        """Test HTTP404 sets a 404 status, the detail, and supports headers."""
        error = HTTP404('Not found')
        assert error.status_code == 404
        assert error.detail == 'Not found'
        assert error.headers is None

        error_with_headers = HTTP404('Not found', headers={'X-Custom': 'value'})
        assert error_with_headers.headers == {'X-Custom': 'value'}

    def test_http409_initialization(self):
        """Test HTTP409 sets a 409 status, the detail, and supports headers."""
        error = HTTP409('Conflict')
        assert error.status_code == 409
        assert error.detail == 'Conflict'
        assert error.headers is None

        error_with_headers = HTTP409('Conflict', headers={'X-Custom': 'value'})
        assert error_with_headers.headers == {'X-Custom': 'value'}

    def test_http409_accepts_dict_detail(self):
        """Test HTTP409 accepts a structured dict detail alongside the 409 status."""
        error = HTTP409({'message': 'Conflict', 'conflicting_id': 42})
        assert error.status_code == 409
        assert error.detail == {'message': 'Conflict', 'conflicting_id': 42}
        assert error.headers is None

    def test_http422_initialization(self):
        """Test HTTP422 sets a 422 status, the detail, and supports headers."""
        error = HTTP422('Unprocessable')
        assert error.status_code == 422
        assert error.detail == 'Unprocessable'
        assert error.headers is None

        error_with_headers = HTTP422('Unprocessable', headers={'X-Custom': 'value'})
        assert error_with_headers.headers == {'X-Custom': 'value'}

    def test_http429_initialization(self):
        """Test HTTP429 sets a 429 status, the detail, and supports headers."""
        error = HTTP429('Too many requests')
        assert error.status_code == 429
        assert error.detail == 'Too many requests'
        assert error.headers is None

        error_with_headers = HTTP429('Too many requests', headers={'Retry-After': '60'})
        assert error_with_headers.headers == {'Retry-After': '60'}

    def test_http500_initialization(self):
        """Test HTTP500 sets a 500 status, the detail, and supports headers."""
        error = HTTP500('Internal server error')
        assert error.status_code == 500
        assert error.detail == 'Internal server error'
        assert error.headers is None

        error_with_headers = HTTP500('Internal server error', headers={'X-Custom': 'value'})
        assert error_with_headers.headers == {'X-Custom': 'value'}

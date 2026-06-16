"""Tests for the /users/me endpoint."""

from fastapi.testclient import TestClient

from app.core.database import DBSession
from tests.conftest import AuthenticatedTestClient


class TestUsersMe:
    def test_returns_current_user(self, admin_client: AuthenticatedTestClient, db: DBSession):
        """An authenticated user gets their own UserBasic shape from /users/me."""
        r = admin_client.get(admin_client.app.url_path_for('users-me'))

        assert r.status_code == 200
        assert r.json() == {
            'id': admin_client.user.id,
            'first_name': admin_client.user.first_name,
            'last_name': admin_client.user.last_name,
            'email': 'admin@test.com',
            'role': 'admin',
            'is_superadmin': False,
            'created_dt': r.json()['created_dt'],
            'updated_dt': r.json()['updated_dt'],
        }

    def test_unauthenticated_is_rejected(self, client: TestClient, db: DBSession):
        """An unauthenticated request to /users/me is rejected with 401."""
        r = client.get(client.app.url_path_for('users-me'))

        assert r.status_code == 401
        assert r.json() == {'detail': 'Not authenticated'}

"""Tests for the /users/me endpoint."""

from fastapi.testclient import TestClient

from app.core.database import DBSession
from tests.auth.factories import ContactFactory
from tests.conftest import AuthenticatedTestClient, _create_authenticated_client_for_user


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
            'user_type': 'admin',
            'is_superadmin': False,
            'created_dt': r.json()['created_dt'],
            'updated_dt': r.json()['updated_dt'],
        }

    def test_returns_contact_user_type(self, client: TestClient, db: DBSession):
        """A CONTACT user's /users/me response carries ``user_type: 'contact'``."""
        contact = ContactFactory.create_with_db(db, email='contact@test.com')
        contact_client = _create_authenticated_client_for_user(client, contact)

        r = contact_client.get(contact_client.app.url_path_for('users-me'))

        assert r.status_code == 200
        assert r.json() == {
            'id': contact.id,
            'first_name': contact.first_name,
            'last_name': contact.last_name,
            'email': 'contact@test.com',
            'user_type': 'contact',
            'is_superadmin': False,
            'created_dt': r.json()['created_dt'],
            'updated_dt': r.json()['updated_dt'],
        }

    def test_unauthenticated_is_rejected(self, client: TestClient, db: DBSession):
        """An unauthenticated request to /users/me is rejected with 401."""
        r = client.get(client.app.url_path_for('users-me'))

        assert r.status_code == 401
        assert r.json() == {'detail': 'Not authenticated'}

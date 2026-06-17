from fastapi.testclient import TestClient

from app.core.database import DBSession
from tests.members.factories import MemberProfileFactory


def _signup_payload(**overrides) -> dict:
    """A minimal valid signup payload."""
    return {'last_name': 'Lovelace', 'email': 'ada@example.com', 'password': 'a-strong-password', **overrides}


class TestMemberSignup:
    def test_signup_creates_a_member(self, client: TestClient, db: DBSession):
        """Public signup creates a member with a generated number and the basic details."""
        r = client.post(
            client.app.url_path_for('members-signup'),
            json=_signup_payload(first_name='Ada', phone='07123456789'),
        )
        assert r.status_code == 201
        data = r.json()
        assert data['member_number'] == f'TTA-{data["id"]:06d}'
        assert data['phone'] == '07123456789'
        assert data['verification_status'] == 'processing'
        assert data['user'] == {
            'id': data['user']['id'],
            'first_name': 'Ada',
            'last_name': 'Lovelace',
            'email': 'ada@example.com',
            'user_type': 'member',
            'is_superadmin': False,
            'created_dt': data['user']['created_dt'],
            'updated_dt': data['user']['updated_dt'],
        }

    def test_signed_up_member_can_log_in(self, client: TestClient, db: DBSession):
        """Unlike a staff-created member, a self-signed-up member can log in with their password."""
        client.post(client.app.url_path_for('members-signup'), json=_signup_payload())
        r = client.post(
            client.app.url_path_for('login'),
            json={'email': 'ada@example.com', 'password': 'a-strong-password'},
        )
        assert r.status_code == 200
        assert r.json()['token_type'] == 'bearer'
        assert r.json()['access_token']

    def test_signup_rejects_duplicate_email(self, client: TestClient, db: DBSession):
        """Signing up with an email that already exists is rejected with 409."""
        MemberProfileFactory.create_with_db(db, email='ada@example.com')
        r = client.post(client.app.url_path_for('members-signup'), json=_signup_payload())
        assert r.status_code == 409
        assert r.json() == {'detail': 'A user with this email already exists'}

    def test_signup_rejects_short_password(self, client: TestClient, db: DBSession):
        """A password below the minimum length is rejected by validation (422)."""
        r = client.post(client.app.url_path_for('members-signup'), json=_signup_payload(password='short'))
        assert r.status_code == 422
        assert any('password' in entry['loc'] for entry in r.json()['detail'])

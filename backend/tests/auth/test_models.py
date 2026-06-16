"""Tests for the access-scoping classmethods and helpers on the ``User`` model."""

from datetime import UTC, datetime
from types import SimpleNamespace

from app.auth.models import User
from app.core.database import DBSession
from tests.auth.factories import AdminFactory, MemberFactory


class TestUserFullName:
    def test_full_name_joins_first_and_last(self):
        """full_name joins the first and last name with a space when both are present."""
        user = User(first_name='Alice', last_name='Smith', email='alice@test.com', role='member')
        assert user.full_name == 'Alice Smith'

    def test_full_name_omits_missing_first_name(self):
        """full_name drops a missing first name and returns just the last name."""
        user = User(first_name=None, last_name='Smith', email='smith@test.com', role='member')
        assert user.full_name == 'Smith'


class TestUserRequestQuery:
    def test_request_query_superadmin_sees_all_non_deleted_users(self, db: DBSession):
        """A superadmin's request_query returns every non-deleted user."""
        member = MemberFactory.create_with_db(db)
        superadmin = AdminFactory.create_with_db(db, is_superadmin=True)

        results = db.exec(User.request_query(_request_for(superadmin))).all()

        assert {member.id, superadmin.id} == {u.id for u in results}

    def test_request_query_member_sees_all_non_deleted_users(self, db: DBSession):
        """A non-superadmin's request_query also returns every non-deleted user (single-tenant)."""
        own = MemberFactory.create_with_db(db)
        other = MemberFactory.create_with_db(db)

        results = db.exec(User.request_query(_request_for(own))).all()

        assert {own.id, other.id} == {u.id for u in results}

    def test_request_query_excludes_deleted_users(self, db: DBSession):
        """request_query excludes soft-deleted users."""
        active = MemberFactory.create_with_db(db)
        deleted = MemberFactory.create_with_db(db, deleted_dt=datetime.now(UTC))

        results = db.exec(User.request_query(_request_for(active))).all()

        result_ids = {u.id for u in results}
        assert active.id in result_ids
        assert deleted.id not in result_ids


def _request_for(user):
    """Build a minimal request-like object carrying ``user`` for the request_query classmethods."""
    return SimpleNamespace(state=SimpleNamespace(user=user))

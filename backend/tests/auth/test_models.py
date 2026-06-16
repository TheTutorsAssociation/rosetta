"""Tests for the helper properties on the ``User`` model."""

from app.auth.models import User


class TestUserFullName:
    def test_full_name_joins_first_and_last(self):
        """full_name joins the first and last name with a space when both are present."""
        user = User(first_name='Alice', last_name='Smith', email='alice@test.com', role='member')
        assert user.full_name == 'Alice Smith'

    def test_full_name_omits_missing_first_name(self):
        """full_name drops a missing first name and returns just the last name."""
        user = User(first_name=None, last_name='Smith', email='smith@test.com', role='member')
        assert user.full_name == 'Smith'

"""Tests for the custom ``DBSession`` and the database module helpers."""

from unittest.mock import Mock, patch

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select

from app.auth.login import get_password_hash
from app.auth.models import User, UserType
from app.common.api.errors import HTTP404
from app.core.database import DBSession, create_db_and_tables, get_db, get_session
from tests.auth.factories import UserFactory


class TestDatabaseModuleHelpers:
    """Test the module-level helpers: ``create_db_and_tables``, ``get_session`` and ``get_db``."""

    @patch('app.core.database.SQLModel')
    @patch('app.core.database.engine')
    def test_create_db_and_tables(self, mock_engine, mock_sqlmodel):
        """Test that ``create_db_and_tables`` creates every SQLModel table on the engine."""
        mock_metadata = Mock()
        mock_sqlmodel.metadata = mock_metadata

        create_db_and_tables()

        mock_metadata.create_all.assert_called_once_with(mock_engine)

    @patch('app.core.database.SQLModel')
    @patch('app.core.database.engine')
    def test_create_db_and_tables_is_idempotent(self, mock_engine, mock_sqlmodel):
        """Test that calling ``create_db_and_tables`` twice simply re-issues ``create_all``."""
        mock_metadata = Mock()
        mock_sqlmodel.metadata = mock_metadata

        create_db_and_tables()
        create_db_and_tables()

        assert mock_metadata.create_all.call_count == 2
        mock_metadata.create_all.assert_called_with(mock_engine)

    @patch('app.core.database.SessionCls')
    def test_get_session(self, mock_session_cls):
        """Test that ``get_session`` returns an instance from ``SessionCls``."""
        mock_session = Mock()
        mock_session_cls.return_value = mock_session

        result = get_session()

        assert result is mock_session
        mock_session_cls.assert_called_once_with()

    @patch('app.core.database.get_session')
    def test_get_db_yields_session_and_closes_on_completion(self, mock_get_session):
        """Test that ``get_db`` yields a session and closes it when the generator finishes."""
        mock_db = Mock()
        mock_get_session.return_value = mock_db

        db_generator = get_db()
        db_session = next(db_generator)

        assert db_session is mock_db
        mock_get_session.assert_called_once_with()

        with pytest.raises(StopIteration):
            next(db_generator)

        mock_db.close.assert_called_once_with()

    @patch('app.core.database.get_session')
    def test_get_db_closes_session_on_exception(self, mock_get_session):
        """Test that ``get_db`` closes the session even when the consumer raises."""
        mock_db = Mock()
        mock_get_session.return_value = mock_db

        db_generator = get_db()
        next(db_generator)

        with pytest.raises(SQLAlchemyError):
            db_generator.throw(SQLAlchemyError('boom'))

        mock_db.close.assert_called_once_with()

    @patch('app.core.database.get_session')
    def test_get_db_closes_session_on_generator_close(self, mock_get_session):
        """Test that ``get_db`` closes the session when the generator is closed early."""
        mock_db = Mock()
        mock_get_session.return_value = mock_db

        db_generator = get_db()
        next(db_generator)
        db_generator.close()

        mock_db.close.assert_called_once_with()

    def test_create_db_and_tables_creates_pg_trgm_extension(self, db: DBSession):
        """Test the real postgres path: ``create_db_and_tables`` creates pg_trgm and the tables."""
        create_db_and_tables()

        result = db.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm'")).fetchone()
        assert result is not None


class TestDBSessionCreate:
    """Test ``DBSession.create``."""

    def test_create_adds_commits_and_refreshes(self, db: DBSession):
        """Test that ``create`` persists the instance and returns it with an assigned id."""
        user = db.create(
            User(
                first_name='Test',
                last_name='User',
                email='create@example.com',
                user_type=UserType.MEMBER,
                hashed_password=get_password_hash('password123'),
            )
        )

        assert user.id is not None
        found = db.exec(select(User).where(User.id == user.id)).one()
        assert {
            'id': found.id,
            'first_name': found.first_name,
            'last_name': found.last_name,
            'email': found.email,
            'user_type': found.user_type,
        } == {
            'id': user.id,
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'create@example.com',
            'user_type': UserType.MEMBER,
        }


class TestDBSessionExists:
    """Test ``DBSession.exists``."""

    def test_exists_returns_true_when_matching_row_present(self, db: DBSession):
        """Test that ``exists`` returns True when a row matches the given filters."""
        user = UserFactory.create_with_db(db, email='exists@example.com')

        assert db.exists(User, email='exists@example.com') is True
        assert db.exists(User, id=user.id) is True

    def test_exists_returns_false_when_no_matching_row(self, db: DBSession):
        """Test that ``exists`` returns False when no row matches the given filters."""
        UserFactory.create_with_db(db, email='exists@example.com')

        assert db.exists(User, email='nobody@example.com') is False


class TestDBSessionGetOr404:
    """Test ``DBSession.get_or_404`` with both a model class and a prebuilt query."""

    def test_get_or_404_returns_instance_for_model(self, db: DBSession):
        """Test that ``get_or_404`` returns the matching instance when passed a model class."""
        user = UserFactory.create_with_db(db, email='found@example.com')

        result = db.get_or_404(User, id=user.id)

        assert result.id == user.id
        assert result.email == 'found@example.com'

    def test_get_or_404_returns_instance_for_query(self, db: DBSession):
        """Test that ``get_or_404`` resolves a prebuilt select query and applies extra filters."""
        user = UserFactory.create_with_db(db, email='query@example.com')

        result = db.get_or_404(select(User), id=user.id)

        assert result.id == user.id
        assert result.email == 'query@example.com'

    def test_get_or_404_raises_for_missing_model(self, db: DBSession):
        """Test that ``get_or_404`` raises HTTP404 with the model name when nothing matches."""
        UserFactory.create_with_db(db, email='present@example.com')

        with pytest.raises(HTTP404) as exc_info:
            db.get_or_404(User, id=999999)

        assert exc_info.value.detail == 'User not found'

    def test_get_or_404_raises_for_missing_query(self, db: DBSession):
        """Test that ``get_or_404`` raises HTTP404 with the column name when a query matches nothing."""
        with pytest.raises(HTTP404) as exc_info:
            db.get_or_404(select(User), id=999999)

        assert exc_info.value.detail == 'User not found'


class TestDBSessionGetOrCreate:
    """Test ``DBSession.get_or_create``."""

    def test_get_or_create_creates_new_instance(self, db: DBSession):
        """Test that ``get_or_create`` creates and returns a new instance when none exists."""
        result, created = db.get_or_create(
            User,
            email='brand-new@example.com',
            defaults={
                'last_name': 'New',
                'user_type': UserType.MEMBER,
                'is_superadmin': True,
                'hashed_password': get_password_hash('password123'),
            },
        )

        assert created is True
        assert result.id is not None
        assert result.email == 'brand-new@example.com'
        assert result.is_superadmin is True

    def test_get_or_create_returns_existing_instance(self, db: DBSession):
        """Test that ``get_or_create`` returns the existing instance without applying defaults."""
        user = UserFactory.create_with_db(db, email='existing@example.com', is_superadmin=False)

        result, created = db.get_or_create(User, email='existing@example.com', defaults={'is_superadmin': True})

        assert created is False
        assert result.id == user.id
        assert result.is_superadmin is False

    def test_get_or_create_handles_integrity_error(self, db: DBSession):
        """Test that ``get_or_create`` recovers from a concurrent-insert IntegrityError.

        The unique ``User.email`` already exists, but the initial lookup is patched to miss
        (simulating the row not yet visible), so the real INSERT raises an IntegrityError and
        the retry SELECT finds the existing row.
        """
        existing = UserFactory.create_with_db(db, email='race@example.com')

        real_exec = db.exec
        call_count = 0

        def exec_missing_first(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                empty = Mock()
                empty.one_or_none.return_value = None
                return empty
            return real_exec(*args, **kwargs)

        with patch.object(db, 'exec', side_effect=exec_missing_first):
            result, created = db.get_or_create(
                User,
                email='race@example.com',
                defaults={
                    'last_name': 'Racer',
                    'user_type': UserType.MEMBER,
                    'hashed_password': get_password_hash('password123'),
                },
            )

        assert created is False
        assert result.id == existing.id
        assert result.email == 'race@example.com'


class TestDBSessionCreateOrUpdate:
    """Test ``DBSession.create_or_update``."""

    def test_create_or_update_creates_new_instance(self, db: DBSession):
        """Test that ``create_or_update`` creates a new instance with the given defaults applied."""
        result, created = db.create_or_update(
            User,
            email='fresh@example.com',
            defaults={
                'last_name': 'Fresh',
                'user_type': UserType.MEMBER,
                'is_superadmin': True,
                'hashed_password': get_password_hash('password123'),
            },
        )

        assert created is True
        assert result.id is not None
        assert result.email == 'fresh@example.com'
        assert result.is_superadmin is True

        found = db.exec(select(User).where(User.id == result.id)).one()
        assert found.is_superadmin is True

    def test_create_or_update_updates_existing_instance(self, db: DBSession):
        """Test that ``create_or_update`` updates an existing instance and applies the defaults."""
        user = UserFactory.create_with_db(db, email='update@example.com', is_superadmin=False)
        original_id = user.id

        result, created = db.create_or_update(
            User,
            id=original_id,
            defaults={'is_superadmin': True, 'last_name': 'Updated'},
        )

        assert created is False
        assert result.id == original_id
        assert result.is_superadmin is True
        assert result.last_name == 'Updated'

    def test_create_or_update_handles_integrity_error(self, db: DBSession):
        """Test that ``create_or_update`` recovers from an IntegrityError by updating the existing row.

        The unique ``User.email`` already exists, but the initial lookup is patched to miss, so
        the real INSERT raises an IntegrityError and the retry SELECT finds and updates the row.
        """
        existing = UserFactory.create_with_db(db, email='race-update@example.com')

        real_exec = db.exec
        call_count = 0

        def exec_missing_first(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                empty = Mock()
                empty.one_or_none.return_value = None
                return empty
            return real_exec(*args, **kwargs)

        with patch.object(db, 'exec', side_effect=exec_missing_first):
            result, created = db.create_or_update(
                User,
                email='race-update@example.com',
                defaults={
                    'last_name': 'UpdatedRacer',
                    'user_type': UserType.MEMBER,
                    'hashed_password': get_password_hash('password123'),
                },
            )

        assert created is False
        assert result.id == existing.id
        assert result.last_name == 'UpdatedRacer'

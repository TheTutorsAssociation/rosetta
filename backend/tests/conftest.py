import os
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Generator
from urllib.parse import urlparse

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import NullPool, event, text
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, create_engine

from app.auth.models import User
from app.core import database
from app.core.celery import celery_app
from app.core.config import settings
from app.core.redis import get_redis_client
from app.main import app
from tests.auth.factories import AdminFactory, MemberFactory


def _configure_test_redis() -> None:
    """Give each xdist worker its own Redis DB so parallel workers don't share rate-limit keys.

    ``TEST_REDIS_URL`` (or ``REDIS_URL`` from pyproject's pytest env) is the base; each worker
    bumps the DB number by its index so ``gw0``/``gw1``/... never collide on the same counters.
    """
    base_url = os.getenv('TEST_REDIS_URL') or str(settings.redis_url)
    worker_id = os.environ.get('PYTEST_XDIST_WORKER', '')
    if worker_id and not os.getenv('TEST_REDIS_URL'):
        worker_num = int(worker_id.replace('gw', ''))
        base_url = base_url.rsplit('/', 1)[0] + f'/{worker_num + 2}'
    os.environ['REDIS_URL'] = base_url
    settings.redis_url = base_url  # ty: ignore[invalid-assignment]


_configure_test_redis()


def _get_worktree_suffix() -> str:
    """Return a DB name suffix when running inside a git worktree (not the main checkout).

    A worktree's ``.git`` is a file (pointing at the parent repo) rather than a directory, so
    each worktree gets its own database and parallel checkouts don't trample each other's data.
    """
    project_root = Path(__file__).parent.parent
    git_path = project_root / '.git'
    if git_path.is_file():
        return f'_{project_root.name}'
    return ''


def get_test_database_url() -> str:
    """Return the test database URL, unique per git-worktree and per xdist worker.

    Falls back to ``DATABASE_URL`` (set in pyproject's pytest env) when ``TEST_DATABASE_URL``
    is not provided. The ``PYTEST_XDIST_WORKER`` suffix gives each parallel worker its own
    database so ``TRUNCATE`` in one worker never races another.
    """
    base_url = os.getenv('TEST_DATABASE_URL') or settings.database_url + _get_worktree_suffix()
    worker_id = os.environ.get('PYTEST_XDIST_WORKER', '')
    if worker_id:
        return f'{base_url}_{worker_id}'
    return base_url


def _ensure_database_exists(db_url: str) -> None:
    """Create the per-worker test database if it does not already exist."""
    parsed = urlparse(db_url)
    db_name = parsed.path.lstrip('/')
    maintenance_url = db_url.rsplit('/', 1)[0] + '/postgres'
    temp_engine = create_engine(maintenance_url, isolation_level='AUTOCOMMIT', poolclass=NullPool)
    with temp_engine.connect() as conn:
        result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")).fetchone()
        if not result:
            conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    temp_engine.dispose()


class QueryCounter:
    """Counts the SQL statements executed on a connection within a ``with`` block.

    Attach via ``count_queries(db)`` and assert on ``.count`` to prove a list endpoint has no
    N+1 regression (e.g. the count is identical at ``page_size=1`` and ``page_size=200``).
    """

    def __init__(self, conn):
        self.conn = conn
        self.count = 0
        self.queries: list[str] = []

    def _callback(self, conn, cursor, statement, parameters, context, executemany) -> None:
        self.count += 1
        self.queries.append(statement)

    def __enter__(self) -> 'QueryCounter':
        event.listen(self.conn, 'before_cursor_execute', self._callback)
        return self

    def __exit__(self, *args) -> None:
        event.remove(self.conn, 'before_cursor_execute', self._callback)


@contextmanager
def count_queries(db: database.DBSession) -> Generator[QueryCounter, None, None]:
    """Count the queries executed inside the block.

    Usage::

        with count_queries(db) as counter:
            client.get(...)
        assert counter.count == expected
    """
    counter = QueryCounter(db.get_bind())
    with counter:
        yield counter


class AuthenticatedTestClient(TestClient):
    """A ``TestClient`` that injects ``Authorization: Bearer <jwt>`` on every verb.

    Stores the underlying ``user`` so tests can reference ``client.user.id`` etc. Use the
    role-specific fixtures (``admin_client``/``member_client``); default to ``auth_client``.
    """

    def __init__(self, app, token: str, user: User):
        super().__init__(app)
        self.token = token
        self.user = user
        self._auth_header = {'Authorization': f'Bearer {token}'}

    def get(self, *args, **kwargs):
        headers = {**self._auth_header, **kwargs.pop('headers', {})}
        return super().get(*args, headers=headers, **kwargs)

    def post(self, *args, **kwargs):
        headers = {**self._auth_header, **kwargs.pop('headers', {})}
        return super().post(*args, headers=headers, **kwargs)

    def put(self, *args, **kwargs):
        headers = {**self._auth_header, **kwargs.pop('headers', {})}
        return super().put(*args, headers=headers, **kwargs)

    def patch(self, *args, **kwargs):
        headers = {**self._auth_header, **kwargs.pop('headers', {})}
        return super().patch(*args, headers=headers, **kwargs)

    def delete(self, *args, **kwargs):
        headers = {**self._auth_header, **kwargs.pop('headers', {})}
        return super().delete(*args, headers=headers, **kwargs)

    def options(self, *args, **kwargs):
        headers = {**self._auth_header, **kwargs.pop('headers', {})}
        return super().options(*args, headers=headers, **kwargs)


_test_db_url = get_test_database_url()
_ensure_database_exists(_test_db_url)
os.environ['TEST_DATABASE_URL'] = _test_db_url
engine = create_engine(_test_db_url, poolclass=NullPool, pool_pre_ping=True, pool_recycle=300)
TestingSessionLocal = sessionmaker(class_=database.DBSession, autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True, scope='session')
def create_test_schema():
    """Create the database schema once per session; per-test cleanup is via ``TRUNCATE``.

    Tests build the schema with ``SQLModel.metadata.create_all`` (fast, no migrations), while
    production applies the same schema via Alembic — CI runs ``alembic upgrade head`` to keep
    the initial migration honest. The pg_trgm extension is created up front so ``ilike`` /
    trigram indexes match production.
    """
    with engine.begin() as conn:
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS pg_trgm'))

    SQLModel.metadata.drop_all(bind=engine)
    SQLModel.metadata.create_all(bind=engine)
    yield
    SQLModel.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True, scope='session')
def eager_celery():
    """Run Celery tasks synchronously and propagate their exceptions for the whole session."""
    celery_app.conf.update(task_always_eager=True, task_eager_propagates=True, task_store_eager_result=True)
    yield


@pytest.fixture(autouse=True)
def clear_redis():
    """Flush the worker's Redis DB before and after each test.

    Rate-limit counters (the per-IP login throttle) live in Redis, so they must be cleared
    between tests or one test's attempts leak into the next and trigger spurious 429s. Failures
    are swallowed so a Redis hiccup never masks the real test result.
    """
    try:
        get_redis_client().flushdb()
    except Exception:
        pass
    yield
    try:
        get_redis_client().flushdb()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def use_test_session_factory(monkeypatch):
    """Point ``database.SessionCls`` at the test session factory.

    ``get_session()`` (used by Celery tasks and scripts) reads ``SessionCls``, so this makes
    tasks dispatched in tests use the test database rather than the production engine.
    """
    monkeypatch.setattr(database, 'SessionCls', TestingSessionLocal)


@pytest.fixture(name='db')
def session_fixture(create_test_schema) -> Generator[database.DBSession, None, None]:
    """Yield a session with fast inter-test cleanup via ``TRUNCATE ... RESTART IDENTITY``.

    Truncating is 100-500x faster than dropping/recreating the schema and gives the same
    isolation. ``RESTART IDENTITY`` resets primary keys, so tests must never hardcode ids.
    """
    db = TestingSessionLocal()

    existing_tables = db.execute(
        text(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' "
            "AND tablename NOT LIKE 'pg_%' AND tablename NOT LIKE 'sql_%'"
        )
    ).fetchall()
    if existing_tables:
        table_names = [table[0] for table in existing_tables]
        tables_str = ', '.join(f'"{name}"' for name in table_names)
        db.execute(text(f'TRUNCATE {tables_str} RESTART IDENTITY CASCADE'))
        db.commit()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture(name='client')
def client_fixture(db: database.DBSession) -> Generator[TestClient, None, None]:
    """An unauthenticated ``TestClient`` whose ``get_db`` dependency uses the test session."""

    def _get_session_override():
        return db

    app.dependency_overrides[database.get_db] = _get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def _create_authenticated_client_for_user(client: TestClient, user: User) -> AuthenticatedTestClient:
    """Mint a web JWT carrying the ``(id, email, user_type)`` triple and wrap it in a client."""
    assert user.id is not None
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode = {'exp': expire, 'email': user.email, 'user_type': user.user_type.value, 'id': user.id}
    token = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return AuthenticatedTestClient(client.app, token, user)


@pytest.fixture(name='admin_client')
def admin_client_fixture(client: TestClient, db: database.DBSession) -> AuthenticatedTestClient:
    """An authenticated client for an ADMIN user."""
    admin = AdminFactory.create_with_db(db, email='admin@test.com')
    return _create_authenticated_client_for_user(client, admin)


@pytest.fixture(name='member_client')
def member_client_fixture(client: TestClient, db: database.DBSession) -> AuthenticatedTestClient:
    """An authenticated client for a MEMBER user."""
    member = MemberFactory.create_with_db(db, email='member@test.com')
    return _create_authenticated_client_for_user(client, member)


@pytest.fixture(name='auth_client')
def auth_client_fixture(admin_client: AuthenticatedTestClient) -> AuthenticatedTestClient:
    """The default client for API tests — admin-level access per the house convention.

    Use the role-specific fixtures only when explicitly testing permission restrictions.
    """
    return admin_client

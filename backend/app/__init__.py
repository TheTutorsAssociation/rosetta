"""Application package.

Importing every model module here guarantees that ``SQLModel.metadata`` is fully
populated before anything that reads it runs — Alembic autogenerate (which diffs the
metadata against the database) and the test suite's ``create_test_schema`` (which calls
``SQLModel.metadata.create_all``). If a model is not imported somewhere on the path to
those entry points, its table silently disappears from the diff/schema, so we register
them all here once.
"""

from app.auth.models import User  # noqa: F401

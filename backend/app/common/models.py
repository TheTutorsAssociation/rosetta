from typing import Optional

from sqlmodel import SQLModel
from sqlmodel.sql._expression_select_cls import SelectOfScalar
from starlette.requests import Request

from app.core.database import DBSession


class AppModel(SQLModel):
    """Abstract base for all domain models.

    Every concrete table model overrides ``request_query`` to return the rows the current
    request may access. Centralising access control on the model keeps these filters out of
    individual endpoints, where they tend to drift.
    """

    @classmethod
    def request_query(cls, request: Request, db: Optional[DBSession] = None) -> SelectOfScalar:
        """Return the query of all rows the current request may access.

        Should return a Select object. ``db`` is passed through in case an override needs a
        separate query to build the scope.
        """
        raise NotImplementedError

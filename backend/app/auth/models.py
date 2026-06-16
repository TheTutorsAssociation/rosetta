from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import EmailStr
from sqlmodel import Field, select
from sqlmodel.sql._expression_select_cls import SelectOfScalar
from starlette.requests import Request

from app.common.fields import EnumField, UTCDatetimeField
from app.common.models import AppModel
from app.core.database import DBSession


class UserRole(str, Enum):
    """A user's role on the platform.

    ``ADMIN`` is TTA staff who manage the platform; ``MEMBER`` is a member-hub user. Elevated
    access is the separate ``is_superadmin`` flag, not a role — so a superadmin can also carry a
    normal role. Extend this enum (and ``app.auth.permissions``) to add finer-grained roles.
    """

    ADMIN = 'admin'
    MEMBER = 'member'


class _User(AppModel):
    """Shared, non-secret user fields.

    ``hashed_password`` is intentionally absent here and declared only on the ``User`` table
    class so it can never leak through a response schema that inherits from ``_User``.
    """

    first_name: Optional[str] = None
    last_name: str
    email: EmailStr = Field(description='Login identifier, unique across all users')
    role: UserRole = EnumField(UserRole)
    is_superadmin: bool = Field(default=False, description='Elevated access that bypasses role checks')
    created_dt: datetime = UTCDatetimeField(now_add=True, index=True)
    updated_dt: Optional[datetime] = UTCDatetimeField(auto_now=True)
    deleted_dt: Optional[datetime] = UTCDatetimeField(
        default=None, exclude=True, description='When the user was anonymised/deleted'
    )

    @property
    def full_name(self) -> str:
        """Return the user's full name, joining first and last name when both are present."""
        parts = [p for p in (self.first_name, self.last_name) if p]
        return ' '.join(parts)

    @property
    def is_admin(self) -> bool:
        """Whether the user has the ADMIN role (does not account for superadmin)."""
        return self.role == UserRole.ADMIN


class User(_User, table=True):
    """The user table for TTA staff and member-hub logins."""

    id: Optional[int] = Field(default=None, primary_key=True)
    email: EmailStr = Field(unique=True, index=True, description='Login identifier, unique across all users')
    hashed_password: str = Field(description='Argon2 password hash; never serialised to a response')

    @classmethod
    def request_query(cls, request: Request, db: DBSession = None) -> SelectOfScalar['User']:  # ty: ignore[invalid-method-override, invalid-parameter-default]
        """Users the requesting user may see.

        Single-tenant: everyone sees all non-deleted users. ``request`` is kept in the
        signature for the ``AppModel`` contract even though access is not request-scoped.
        """
        return select(User).where(User.deleted_dt == None)  # noqa: E711


class UserBasic(_User):
    """Public-facing user shape used in responses — carries the id but never the password hash."""

    id: int

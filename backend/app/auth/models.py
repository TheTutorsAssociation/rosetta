from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import EmailStr
from sqlalchemy import Index
from sqlmodel import Field

from app.common.fields import EnumField, UTCDatetimeField
from app.common.models import AppModel


class UserType(str, Enum):
    """The kind of login user on the platform.

    Three user types: ``ADMIN`` is TTA staff who manage the platform; ``MEMBER`` is a member-hub
    user; ``CONTACT`` is a non-member who can still log in. Elevated access is the separate
    ``is_superadmin`` flag, not a user type — so a superadmin can also carry a normal user type.
    Extend this enum (and ``app.auth.permissions``) to add finer-grained user types.
    """

    ADMIN = 'admin'
    MEMBER = 'member'
    CONTACT = 'contact'


class _User(AppModel):
    """Shared, non-secret user fields.

    ``hashed_password`` is intentionally absent here and declared only on the ``User`` table
    class so it can never leak through a response schema that inherits from ``_User``.
    """

    first_name: Optional[str] = None
    last_name: str = Field(index=True)  # B-tree: sorted in the members list
    email: EmailStr = Field(description='Login identifier, unique across all users')
    user_type: UserType = EnumField(UserType)
    is_superadmin: bool = Field(default=False, description='Elevated access that bypasses user-type checks')
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
        """Whether the user is of the ADMIN type (does not account for superadmin)."""
        return self.user_type == UserType.ADMIN


class User(_User, table=True):
    """The user table for TTA staff and member-hub logins."""

    # pg_trgm GIN indexes for the members-list ILIKE search (a B-tree can't serve `%term%`).
    __table_args__ = (
        Index(
            'ix_user_first_name_trgm',
            'first_name',
            postgresql_using='gin',
            postgresql_ops={'first_name': 'gin_trgm_ops'},
        ),
        Index(
            'ix_user_last_name_trgm', 'last_name', postgresql_using='gin', postgresql_ops={'last_name': 'gin_trgm_ops'}
        ),
        Index('ix_user_email_trgm', 'email', postgresql_using='gin', postgresql_ops={'email': 'gin_trgm_ops'}),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    email: EmailStr = Field(unique=True, index=True, description='Login identifier, unique across all users')
    hashed_password: str = Field(description='Argon2 password hash; never serialised to a response')


class UserBasic(_User):
    """Public-facing user shape used in responses — carries the id but never the password hash."""

    id: int

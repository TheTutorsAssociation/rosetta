import factory

from app.auth.login import get_password_hash
from app.auth.models import User, UserRole
from tests.base_factory import SQLModelFactory

DEFAULT_PASSWORD = 'testing-password'


class UserFactory(SQLModelFactory):
    """Factory for a MEMBER ``User``.

    All roles share a known password (``DEFAULT_PASSWORD``) so login tests can authenticate
    without re-hashing.
    """

    class Meta:
        model = User

    first_name = factory.Faker('first_name')
    last_name = factory.Sequence(lambda n: f'User_{n}')
    role = UserRole.MEMBER
    is_superadmin = False
    hashed_password = factory.LazyFunction(lambda: get_password_hash(DEFAULT_PASSWORD))

    @factory.LazyAttribute
    def email(self):
        """Derive a unique email from the first and last name."""
        return f'{self.first_name}_{self.last_name}@example.com'.lower().replace(' ', '_')


class AdminFactory(UserFactory):
    """Factory for an ADMIN ``User``."""

    last_name = factory.Sequence(lambda n: f'Admin_{n}')
    role = UserRole.ADMIN


class MemberFactory(UserFactory):
    """Factory for a MEMBER ``User`` (explicit alias of the base member role)."""

    last_name = factory.Sequence(lambda n: f'Member_{n}')
    role = UserRole.MEMBER

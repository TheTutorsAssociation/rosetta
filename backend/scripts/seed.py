"""Seed a single development superadmin user.

Idempotent: re-running it never creates a duplicate. Reads ``SEED_ADMIN_EMAIL`` /
``SEED_ADMIN_PASSWORD`` from the environment, falling back to dev defaults. Run with
``uv run python scripts/seed.py``.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.auth.login import get_password_hash  # noqa: E402
from app.auth.models import User, UserType  # noqa: E402
from app.core.database import get_session  # noqa: E402

SEED_ADMIN_EMAIL = os.getenv('SEED_ADMIN_EMAIL', 'admin@example.com')
SEED_ADMIN_PASSWORD = os.getenv('SEED_ADMIN_PASSWORD', 'rosetta-dev-password')


def seed() -> None:
    """Create the dev superadmin if it does not already exist."""
    with get_session() as db:
        user, created = db.get_or_create(
            User,
            email=SEED_ADMIN_EMAIL,
            defaults={
                'first_name': 'Rosetta',
                'last_name': 'Admin',
                'user_type': UserType.ADMIN,
                'is_superadmin': True,
                'hashed_password': get_password_hash(SEED_ADMIN_PASSWORD),
            },
        )
    action = 'created' if created else 'already exists'
    print(f'Superadmin {user.email} {action}.')


if __name__ == '__main__':
    seed()

import factory

from app.members.models.member import Member, VerificationStatus, generate_member_number
from tests.auth.factories import UserFactory
from tests.base_factory import SQLModelFactory


class MemberProfileFactory(SQLModelFactory):
    """Create a member = a ``User(MEMBER)`` + its 1:1 ``Member`` profile (with a member_number).

    Distinct from ``tests.auth.factories.MemberFactory``, which is a bare ``User(MEMBER)`` used
    only for permission-boundary tests.
    """

    class Meta:
        model = Member

    phone = factory.Sequence(lambda n: f'0700000{n:04d}')
    verification_status = VerificationStatus.PROCESSING

    @classmethod
    def create_with_db(cls, db, *, user=None, first_name=None, last_name=None, email=None, **kwargs):
        """Create the underlying ``User(MEMBER)`` (unless ``user=`` is passed), then the profile."""
        if user is None:
            user_kwargs = {
                key: value
                for key, value in (('first_name', first_name), ('last_name', last_name), ('email', email))
                if value is not None
            }
            user = UserFactory.create_with_db(db, **user_kwargs)
        member = super().create_with_db(db, user_id=user.id, **kwargs)
        member.member_number = generate_member_number(member.id)
        db.add(member)
        db.commit()
        db.refresh(member)
        return member

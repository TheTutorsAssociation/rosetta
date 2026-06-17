from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.auth.login import MAX_PASSWORD_LENGTH, get_password_hash
from app.auth.models import User, UserType
from app.common.api.errors import HTTP409
from app.common.api.rate_limit import rate_limit_by_ip
from app.core.database import DBSession, get_db
from app.members.models.member import Member, MemberBasic, generate_member_number

anon_router = APIRouter(prefix='/members', tags=['members', 'anon'])

# A signup password must be usable (unlike a staff-created member's), so bound it sensibly: long
# enough to resist guessing, capped at MAX_PASSWORD_LENGTH so the argon2 hash can't be made huge.
MIN_SIGNUP_PASSWORD_LENGTH = 8


class MemberSignup(BaseModel):
    """Public member-signup request: basic details + a chosen password."""

    first_name: str | None = None
    last_name: str
    email: EmailStr
    phone: str | None = None
    password: str = Field(min_length=MIN_SIGNUP_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)

    model_config = ConfigDict(
        json_schema_extra={
            'example': {
                'first_name': 'Ada',
                'last_name': 'Lovelace',
                'email': 'ada@example.com',
                'phone': '07123456789',
                'password': 'a-strong-password',
            }
        }
    )


@anon_router.post(
    '/signup',
    response_model=MemberBasic,
    status_code=201,
    name='members-signup',
    dependencies=[Depends(rate_limit_by_ip('signup', window_seconds=60, max_attempts=5))],
)
def signup(body: MemberSignup, db: DBSession = Depends(get_db)) -> MemberBasic:
    """Public self-service signup: create a ``User(MEMBER)`` with a real password + its profile.

    Unlike the admin-created member (which gets an unusable password), the signing-up member sets
    their own password and can log in immediately. Staff verification (``verification_status``)
    still defaults to ``PROCESSING``.
    """
    if db.exists(User, email=body.email):
        raise HTTP409('A user with this email already exists')

    user = User(
        first_name=body.first_name,
        last_name=body.last_name,
        email=body.email,
        user_type=UserType.MEMBER,
        hashed_password=get_password_hash(body.password),
    )
    db.add(user)
    db.flush()
    member = Member(user_id=user.id, phone=body.phone)  # ty:ignore[invalid-argument-type]
    db.add(member)
    db.flush()
    member.member_number = generate_member_number(member.id)  # ty:ignore[invalid-argument-type]
    db.commit()
    db.refresh(member)
    return MemberBasic.model_validate(member, from_attributes=True)

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, or_
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.sql._expression_select_cls import SelectOfScalar

from app.auth.login import make_unusable_password
from app.auth.models import User, UserType
from app.common.api.errors import HTTP404, HTTP409
from app.common.api.filters import ListFilter, ListOrder, OrderDirection
from app.common.api.paginate import PaginatedResponse
from app.common.utils import escape_like
from app.core.config import settings
from app.core.database import DBSession, get_db
from app.members.models.member import (
    Member,
    MemberBasic,
    MemberCreate,
    MemberUpdate,
    VerificationStatus,
    generate_member_number,
)

router = APIRouter(prefix='/members', tags=['members'])

# Filters that depend on later models — product (#8), company (#7), tag (#10) — and the computed
# compliance RAG (#13) are deferred to those issues; #5 ships only what the Member model can answer.


class MemberListFilter(ListFilter):
    """Query filters for the member list."""

    status: Optional[VerificationStatus] = None
    search: Optional[str] = None
    new_in_days: Optional[int] = None

    def apply(self, query: SelectOfScalar, user: User) -> SelectOfScalar:
        if self.status is not None:
            query = query.where(Member.verification_status == self.status)
        if self.search:
            pattern = f'%{escape_like(self.search)}%'
            query = query.where(
                or_(
                    User.first_name.ilike(pattern),  # ty:ignore[unresolved-attribute]
                    User.last_name.ilike(pattern),  # ty:ignore[unresolved-attribute]
                    User.email.ilike(pattern),  # ty:ignore[unresolved-attribute]
                    Member.member_number.ilike(pattern),  # ty:ignore[unresolved-attribute]
                )
            )
        if self.new_in_days is not None:
            query = query.where(Member.created_dt >= datetime.now(UTC) - timedelta(days=self.new_in_days))
        return query


@dataclass
class MemberListOrder(ListOrder):
    """Ordering for the member list. ``last_name`` lives on the joined ``User``, ``created_dt`` on ``Member``."""

    model = Member
    fields = ['created_dt', 'last_name']
    order_direction = OrderDirection.DESC

    def apply(self, query: SelectOfScalar, user: User | None = None) -> SelectOfScalar:
        order_by_field = self.order_by.value if self.order_by else self.fields[0]  # ty:ignore[unresolved-attribute]
        column = User.last_name if order_by_field == 'last_name' else Member.created_dt
        clause = column.desc() if self.order_direction == OrderDirection.DESC else column.asc()  # ty:ignore[unresolved-attribute]
        return query.order_by(clause).order_by(Member.id.asc())  # ty:ignore[unresolved-attribute]


@router.options('', name='members-list-options')
def member_list_options() -> dict:
    """Filter + ordering discovery for the member list (consumed by the admin UI)."""
    return {**MemberListFilter.get_options(), **MemberListOrder.get_options()}


@router.get('', response_model=PaginatedResponse[MemberBasic], name='members-list')
def list_members(
    request: Request,
    filters: MemberListFilter = Depends(),
    ordering: MemberListOrder = Depends(MemberListOrder),
    db: DBSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: Optional[int] = Query(None, ge=1, le=200),
) -> PaginatedResponse[MemberBasic]:
    """List members (paginate-then-fetch: page subset first, then eager-load each member's user)."""
    resolved_page_size = page_size or settings.dft_page_size
    base_query = ordering.apply(filters.apply(Member.request_query(request, db), request.state.user))
    page_members = db.exec(base_query.limit(resolved_page_size).offset((page - 1) * resolved_page_size)).all()

    if page_members:
        member_ids = [m.id for m in page_members]
        loaded = db.exec(
            Member.request_query(request, db)
            .options(selectinload(Member.user))  # ty:ignore[invalid-argument-type]
            .where(Member.id.in_(member_ids))  # ty:ignore[unresolved-attribute]
        ).all()
        by_id = {m.id: m for m in loaded}
        items = [MemberBasic.model_validate(by_id[mid], from_attributes=True) for mid in member_ids]
    else:
        items = []

    total = db.exec(select(func.count()).select_from(base_query.order_by(None).subquery())).one()
    return PaginatedResponse[MemberBasic](items=items, total=total, page=page, page_size=resolved_page_size)


@router.post('', response_model=MemberBasic, status_code=201, name='members-create')
def create_member(request: Request, body: MemberCreate, db: DBSession = Depends(get_db)) -> MemberBasic:
    """Create a member = a ``User(MEMBER)`` (with an unusable password) + its 1:1 profile."""
    if db.exists(User, email=body.email):
        raise HTTP409('A user with this email already exists')

    profile = body.model_dump(exclude={'first_name', 'last_name', 'email'})
    user = User(
        first_name=body.first_name,
        last_name=body.last_name,
        email=body.email,
        user_type=UserType.MEMBER,
        hashed_password=make_unusable_password(),
    )
    db.add(user)
    db.flush()
    member = Member(user_id=user.id, **profile)  # ty:ignore[invalid-argument-type]
    db.add(member)
    db.flush()
    member.member_number = generate_member_number(member.id)  # ty:ignore[invalid-argument-type]
    db.commit()
    db.refresh(member)
    return MemberBasic.model_validate(member, from_attributes=True)


@router.get('/{member_id}', response_model=MemberBasic, name='members-detail')
def get_member(member_id: int, request: Request, db: DBSession = Depends(get_db)) -> MemberBasic:
    member = db.exec(
        Member.request_query(request, db).options(selectinload(Member.user)).where(Member.id == member_id)  # ty:ignore[invalid-argument-type]
    ).first()
    if not member:
        raise HTTP404('Member not found')
    return MemberBasic.model_validate(member, from_attributes=True)


@router.patch('/{member_id}', response_model=MemberBasic, name='members-update')
def update_member(member_id: int, request: Request, body: MemberUpdate, db: DBSession = Depends(get_db)) -> MemberBasic:
    member = db.exec(Member.request_query(request, db).where(Member.id == member_id)).first()
    if not member:
        raise HTTP404('Member not found')

    data = body.model_dump(exclude_unset=True)
    for field in ('first_name', 'last_name', 'email'):
        if field in data:
            setattr(member.user, field, data.pop(field))
    for field, value in data.items():
        setattr(member, field, value)
    db.commit()
    db.refresh(member)
    return MemberBasic.model_validate(member, from_attributes=True)


@router.delete('/{member_id}', status_code=204, name='members-delete')
def delete_member(member_id: int, request: Request, db: DBSession = Depends(get_db)) -> None:
    member = db.exec(Member.request_query(request, db).where(Member.id == member_id)).first()
    if not member:
        raise HTTP404('Member not found')
    member.user.deleted_dt = datetime.now(UTC)
    db.commit()

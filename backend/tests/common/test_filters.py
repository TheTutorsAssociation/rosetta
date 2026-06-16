from dataclasses import dataclass, field
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import List, Optional

import pytest
from pydantic import Field as PydanticField
from sqlmodel import select

from app.auth.models import User, UserRole
from app.common.api.errors import HTTP422
from app.common.api.filters import FKFilterField, FKIntMeta, ListFilter, ListOrder, OrderDirection
from app.common.utils import escape_like, inclusive_end_of_day
from tests.auth.factories import AdminFactory, UserFactory


def _request_for(user):
    """Build a minimal request-like object carrying ``user`` for the request_query classmethods."""
    return SimpleNamespace(state=SimpleNamespace(user=user))


@dataclass
class _UserListOrder(ListOrder):
    """Ordering for the user list, sorted by name then created_dt (ascending by default)."""

    model = User
    fields = ['last_name', 'created_dt']
    order_direction: OrderDirection = field(default=OrderDirection.ASC)


@dataclass
class _TiebreakerOrder(ListOrder):
    """Ordering with a non-id tiebreaker field to exercise the secondary-sort branch."""

    model = User
    fields = ['role', 'last_name']
    tiebreaker_fields = ['last_name']
    order_direction = OrderDirection.ASC


@dataclass
class _IdTiebreakerOrder(ListOrder):
    """Ordering whose declared tiebreaker is ``id`` so no extra id tiebreaker is appended."""

    model = User
    fields = ['last_name']
    tiebreaker_fields = ['id']


@dataclass
class _IdPrimaryOrder(ListOrder):
    """Ordering whose primary sort is ``id`` so no extra id tiebreaker is appended."""

    model = User
    fields = ['id', 'last_name']


class _UserListFilter(ListFilter):
    """Query filters for the user list endpoint, exercising search, date range and FK branches."""

    search: str | None = None
    created_from: datetime | None = None
    created_to: datetime | None = None
    user_id: FKFilterField(User, name_field='email') = None  # ty: ignore[invalid-type-form]

    def apply(self, query, user):
        """Apply the configured filters to ``query``."""
        if self.search:
            query = query.where(User.last_name.ilike(f'%{escape_like(self.search)}%'))
        if self.created_from:
            query = query.where(User.created_dt >= self.created_from)
        if self.created_to:
            query = query.where(User.created_dt <= inclusive_end_of_day(self.created_to))
        if self.user_id:
            query = query.where(User.id == self.user_id)
        return query


class _EnumAndListFilter(ListFilter):
    """A filter exposing an Enum and a list field to exercise both ``get_options`` branches."""

    role: Optional[UserRole] = PydanticField(default=None)
    tags: Optional[List[str]] = PydanticField(default=None)
    name: str = PydanticField()

    def apply(self, query, user):
        """Unused — this filter only exercises ``get_options`` and ``get_field_type``."""
        return query


class TestOrderDirection:
    """Tests for the OrderDirection enum."""

    def test_values(self):
        """The enum exposes asc/desc string members."""
        assert OrderDirection.ASC.value == 'asc'
        assert OrderDirection.DESC.value == 'desc'
        assert [d.value for d in OrderDirection] == ['asc', 'desc']


class TestListOrderApply:
    """Tests for ListOrder.apply ordering behaviour against seeded users."""

    def test_default_order_uses_first_field_and_appends_id_tiebreaker(self, db):
        """With no order_by the first declared field is used, with an id tiebreaker."""
        first = UserFactory.create_with_db(db, last_name='Alpha')
        second = UserFactory.create_with_db(db, last_name='Zeta')

        query = _UserListOrder().apply(select(User))
        results = db.exec(query).all()

        assert [u.id for u in results] == [first.id, second.id]

    def test_explicit_order_by_ascending(self, db):
        """An explicit order_by with ASC direction orders by that column ascending."""
        alpha = UserFactory.create_with_db(db, last_name='Alpha')
        zeta = UserFactory.create_with_db(db, last_name='Zeta')

        ordering = _UserListOrder(order_by='last_name', order_direction=OrderDirection.ASC)
        results = db.exec(ordering.apply(select(User))).all()

        assert [u.id for u in results] == [alpha.id, zeta.id]

    def test_order_by_accepts_enum_member(self, db):
        """order_by may be passed as the OrderBy enum member directly."""
        alpha = UserFactory.create_with_db(db, last_name='Alpha')
        zeta = UserFactory.create_with_db(db, last_name='Zeta')

        ordering = _UserListOrder(order_by=_UserListOrder.OrderBy.LAST_NAME, order_direction=OrderDirection.ASC)
        results = db.exec(ordering.apply(select(User))).all()

        assert [u.id for u in results] == [alpha.id, zeta.id]

    def test_apply_accepts_unused_user_argument(self, db):
        """apply accepts a user argument for parity with overrides and ignores it."""
        user = UserFactory.create_with_db(db, last_name='Solo')

        results = db.exec(_UserListOrder().apply(select(User), user)).all()

        assert [u.id for u in results] == [user.id]

    def test_tiebreaker_field_breaks_ties_within_primary_sort(self, db):
        """A declared tiebreaker field orders rows sharing the primary sort value ascending."""
        zeta = UserFactory.create_with_db(db, last_name='Zeta', role=UserRole.MEMBER)
        alpha = UserFactory.create_with_db(db, last_name='Alpha', role=UserRole.MEMBER)

        results = db.exec(_TiebreakerOrder().apply(select(User))).all()

        assert [u.id for u in results] == [alpha.id, zeta.id]

    def test_tiebreaker_skipped_when_equal_to_primary_order_field(self, db):
        """When the primary order_by equals a tiebreaker field, that tiebreaker is not duplicated."""
        alpha = UserFactory.create_with_db(db, last_name='Alpha')
        zeta = UserFactory.create_with_db(db, last_name='Zeta')

        ordering = _TiebreakerOrder(order_by='last_name', order_direction=OrderDirection.ASC)
        results = db.exec(ordering.apply(select(User))).all()

        assert [u.id for u in results] == [alpha.id, zeta.id]

    def test_no_id_tiebreaker_appended_when_id_in_tiebreaker_fields(self, db):
        """An id tiebreaker declared explicitly is not appended a second time."""
        first = UserFactory.create_with_db(db, last_name='Alpha')
        second = UserFactory.create_with_db(db, last_name='Alpha')

        results = db.exec(_IdTiebreakerOrder().apply(select(User))).all()

        assert [u.id for u in results] == [first.id, second.id]

    def test_no_id_tiebreaker_appended_when_primary_sort_is_id(self, db):
        """When the primary sort column is id itself, no extra id tiebreaker is appended."""
        first = UserFactory.create_with_db(db, last_name='Alpha')
        second = UserFactory.create_with_db(db, last_name='Zeta')

        ordering = _IdPrimaryOrder(order_by='id', order_direction=OrderDirection.DESC)
        results = db.exec(ordering.apply(select(User))).all()

        assert [u.id for u in results] == [second.id, first.id]

    def test_invalid_order_by_raises_http422(self):
        """An unknown order_by string raises HTTP422 listing the valid fields."""
        with pytest.raises(HTTP422) as exc:
            _UserListOrder(order_by='not_a_field')

        assert exc.value.detail == 'Invalid order_by value. Must be one of: last_name, created_dt'


class TestListOrderSubclassValidation:
    """Tests for ListOrder.__init_subclass__ guard rails."""

    def test_missing_model_or_fields_raises_type_error(self):
        """A subclass without model and fields attributes is rejected at class creation."""
        with pytest.raises(TypeError) as exc:

            @dataclass
            class _BadOrder(ListOrder):
                pass

        assert 'must define model and fields' in str(exc.value)

    def test_non_lowercase_fields_raise_type_error(self):
        """Non-lowercase field names are rejected to avoid Enum key collisions."""
        with pytest.raises(TypeError) as exc:

            @dataclass
            class _UppercaseOrder(ListOrder):
                model = User
                fields = ['Last_name']

        assert 'must be lowercase' in str(exc.value)


class TestListOrderGetOptions:
    """Tests for ListOrder.get_options metadata introspection."""

    def test_returns_order_by_and_direction_metadata(self):
        """get_options returns the choices, default field and default direction."""
        assert _UserListOrder.get_options() == {
            'order_by': {
                'type': 'str',
                'required': False,
                'choices': [{'id': 'last_name', 'name': 'last_name'}, {'id': 'created_dt', 'name': 'created_dt'}],
                'default': 'last_name',
            },
            'order_direction': {
                'type': 'OrderDirection',
                'required': False,
                'choices': [{'id': 'asc', 'name': 'asc'}, {'id': 'desc', 'name': 'desc'}],
                'default': 'asc',
            },
        }


class TestListFilterApply:
    """Tests for ListFilter.apply adding WHERE clauses against seeded users."""

    def test_search_filters_by_name_case_insensitively(self, db):
        """The search filter matches the user last name case-insensitively."""
        match = UserFactory.create_with_db(db, last_name='Zebra')
        UserFactory.create_with_db(db, last_name='Giraffe')
        user = AdminFactory.create_with_db(db)

        query = _UserListFilter(search='zeb').apply(select(User), user)
        results = db.exec(query).all()

        assert [u.id for u in results] == [match.id]

    def test_created_range_bounds_the_query(self, db):
        """created_from and created_to bound the query by creation datetime."""
        inside = UserFactory.create_with_db(db, created_dt=datetime(2024, 1, 1, tzinfo=UTC))
        UserFactory.create_with_db(db, created_dt=datetime(2024, 6, 1, tzinfo=UTC))
        user = AdminFactory.create_with_db(db)

        filters = _UserListFilter(
            created_from=datetime(2023, 12, 1, tzinfo=UTC), created_to=datetime(2024, 2, 1, tzinfo=UTC)
        )
        results = db.exec(filters.apply(select(User), user)).all()

        assert inside.id in {u.id for u in results}
        assert all(r.created_dt <= datetime(2024, 2, 2, tzinfo=UTC) for r in results)

    def test_user_id_narrows_the_query(self, db):
        """The user_id FK filter narrows the query to one user."""
        wanted = UserFactory.create_with_db(db, last_name='Wanted')
        UserFactory.create_with_db(db, last_name='Other')
        admin = AdminFactory.create_with_db(db)

        filters = _UserListFilter(user_id=wanted.id)
        results = db.exec(filters.apply(select(User), admin)).all()

        assert [u.id for u in results] == [wanted.id]

    def test_no_filters_returns_query_unchanged(self, db):
        """With no filters set, apply leaves the query unchanged."""
        user = UserFactory.create_with_db(db)

        results = db.exec(_UserListFilter().apply(select(User), user)).all()

        assert [u.id for u in results] == [user.id]

    def test_base_apply_is_not_implemented(self):
        """The base ListFilter.apply raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            ListFilter().apply(select(User), None)


class TestListFilterGetOptions:
    """Tests for ListFilter.get_options field introspection and FK choice population."""

    def test_populates_fk_choices_via_request_query(self, db):
        """FK fields produce id/name choices scoped by the model's request_query."""
        visible = UserFactory.create_with_db(db, email='visible@example.com')
        user = AdminFactory.create_with_db(db, email='admin@example.com')
        request = _request_for(user)

        options = _UserListFilter.get_options(request, db)

        assert options['search'] == {'type': 'str', 'required': False}
        assert options['created_from'] == {'type': 'datetime', 'required': False}
        assert options['created_to'] == {'type': 'datetime', 'required': False}
        assert options['user_id']['type'] == 'int'
        assert options['user_id']['required'] is False
        choices = {choice['id']: choice['name'] for choice in options['user_id']['choices']}
        assert choices[visible.id] == 'visible@example.com'
        assert choices[user.id] == 'admin@example.com'

    def test_enum_and_list_and_required_field_metadata(self, db):
        """Enum fields produce value choices, list fields unwrap, and required fields are flagged."""
        user = AdminFactory.create_with_db(db)

        assert _EnumAndListFilter.get_options(_request_for(user), db) == {
            'role': {
                'type': 'UserRole',
                'required': False,
                'choices': [
                    {'id': 'admin', 'name': 'admin'},
                    {'id': 'member', 'name': 'member'},
                ],
            },
            'tags': {'type': 'str', 'required': False},
            'name': {'type': 'str', 'required': True},
        }


class TestGetFieldType:
    """Tests for ListFilter.get_field_type unwrapping Optional, unions and lists."""

    def test_unwraps_optional_field(self):
        """An Optional[str] field unwraps to str."""
        field_info = _UserListFilter.model_fields['search']
        assert ListFilter.get_field_type(field_info) is str

    def test_unwraps_pipe_union_field(self):
        """A ``str | None`` field unwraps to str via the UnionType branch."""

        class _PipeFilter(ListFilter):
            value: str | None = PydanticField(default=None)

            def apply(self, query, user):
                """Unused."""
                return query

        field_info = _PipeFilter.model_fields['value']
        assert ListFilter.get_field_type(field_info) is str

    def test_unwraps_list_field(self):
        """A list field unwraps to its element type."""
        field_info = _EnumAndListFilter.model_fields['tags']
        assert ListFilter.get_field_type(field_info) is str


class TestFKFilterField:
    """Tests for FKFilterField / FKIntMeta producing the annotated FK type."""

    def test_default_name_field(self):
        """FKFilterField attaches FKIntMeta with the default name field."""
        annotated = FKFilterField(User)
        meta = annotated.__metadata__[0]
        assert isinstance(meta, FKIntMeta)
        assert meta.model is User
        assert meta.name_field == 'name'

    def test_custom_name_field(self):
        """FKFilterField honours a custom name_field."""
        annotated = FKFilterField(User, name_field='email')
        meta = annotated.__metadata__[0]
        assert meta.model is User
        assert meta.name_field == 'email'

from typing import Optional

import pytest
from sqlmodel import select

from app.auth.models import User
from app.common.api.errors import HTTP422
from app.common.api.filters import ListFilter, ListOrder, OrderDirection
from app.members.models.member import VerificationStatus


class _UserOrder(ListOrder):
    """Order ``User`` by last_name/created_dt, with an ``email`` tiebreaker."""

    model = User
    fields = ['last_name', 'created_dt']
    tiebreaker_fields = ['email']


class _IdOrder(ListOrder):
    """Order whose primary field is ``id`` (so no extra id tiebreaker is appended)."""

    model = User
    fields = ['id', 'last_name']


class _ProbeFilter(ListFilter):
    """A filter exercising every ``get_field_type`` branch + the enum-choices path."""

    required_field: int
    opt_int: Optional[int] = None
    pipe_int: int | None = None
    tags: list[str] = []
    status: Optional[VerificationStatus] = None


class TestListOrderSubclassValidation:
    def test_missing_model_and_fields_raises(self):
        """A ListOrder subclass without model/fields is rejected at definition time."""
        with pytest.raises(TypeError, match='must define model and fields'):

            class _Bad(ListOrder):
                pass

    def test_non_lowercase_fields_raise(self):
        """Field names must be lowercase to avoid Enum key collisions."""
        with pytest.raises(TypeError, match='must be lowercase'):

            class _BadCase(ListOrder):
                model = User
                fields = ['LastName']


class TestListOrderApply:
    def test_default_order_uses_first_field_descending(self):
        """With no order_by, the first field is used in the default DESC direction."""
        order = _UserOrder()
        result = order.apply(select(User))
        assert result is not None

    def test_explicit_order_by_ascending(self):
        """An explicit order_by + ASC direction is honoured, with the email + id tiebreakers."""
        order = _UserOrder(order_by='last_name', order_direction=OrderDirection.ASC)
        result = order.apply(select(User))
        assert result is not None

    def test_invalid_order_by_raises_422(self):
        """An order_by outside the declared fields raises HTTP422."""
        with pytest.raises(HTTP422, match='Invalid order_by value'):
            _UserOrder(order_by='nonsense')

    def test_id_primary_sort_skips_extra_id_tiebreaker(self):
        """When the primary sort is already id, no duplicate id tiebreaker is appended."""
        order = _IdOrder()
        result = order.apply(select(User))
        assert result is not None

    def test_get_options_lists_fields_and_directions(self):
        """get_options exposes the orderable fields and directions for OPTIONS discovery."""
        options = _UserOrder.get_options()
        assert options['order_by']['choices'] == [
            {'id': 'last_name', 'name': 'last_name'},
            {'id': 'created_dt', 'name': 'created_dt'},
        ]
        assert options['order_by']['default'] == 'last_name'
        assert options['order_direction']['default'] == 'desc'


class TestListFilterOptions:
    def test_get_options_resolves_types_and_enum_choices(self):
        """get_options reports each field's type, requiredness and (for enums) value choices."""
        options = _ProbeFilter.get_options()
        assert options['required_field'] == {'type': 'int', 'required': True}
        assert options['opt_int'] == {'type': 'int', 'required': False}
        assert options['pipe_int'] == {'type': 'int', 'required': False}
        assert options['tags'] == {'type': 'str', 'required': False}
        assert options['status'] == {
            'type': 'VerificationStatus',
            'required': False,
            'choices': [{'id': 'processing', 'name': 'processing'}, {'id': 'verified', 'name': 'verified'}],
        }

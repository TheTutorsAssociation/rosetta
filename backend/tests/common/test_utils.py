from datetime import datetime

from app.common.utils import escape_like, inclusive_end_of_day


class TestEscapeLike:
    """Test the escape_like function for SQL LIKE pattern escaping."""

    def test_escapes_percent_character(self):
        """Test that percent signs are escaped."""
        assert escape_like('%match%') == '\\%match\\%'

    def test_escapes_underscore_character(self):
        """Test that underscores are escaped."""
        assert escape_like('test_value') == 'test\\_value'

    def test_escapes_backslash_character(self):
        """Test that backslashes are escaped."""
        assert escape_like('path\\to\\file') == 'path\\\\to\\\\file'

    def test_escapes_multiple_special_characters(self):
        """Test that multiple special characters in one string are all escaped."""
        assert escape_like('100% of _users\\data') == '100\\% of \\_users\\\\data'

    def test_preserves_normal_text(self):
        """Test that normal text without special characters is unchanged."""
        assert escape_like('Mathematics 101') == 'Mathematics 101'

    def test_handles_empty_string(self):
        """Test that empty string returns empty string."""
        assert escape_like('') == ''


class TestInclusiveEndOfDay:
    """Test inclusive_end_of_day bumps midnight datetimes and passes explicit times through."""

    def test_bumps_midnight_to_end_of_day(self):
        """Test that a date-only datetime is bumped to 23:59:59.999999 the same day."""
        assert inclusive_end_of_day(datetime(2024, 3, 15)) == datetime(2024, 3, 15, 23, 59, 59, 999999)

    def test_passes_explicit_time_through_unchanged(self):
        """Test that a datetime with an explicit time is returned verbatim."""
        dt = datetime(2024, 3, 15, 10, 30, 0)
        assert inclusive_end_of_day(dt) == dt

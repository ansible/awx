import pytest

from rest_framework.fields import ValidationError

from awx.conf.fields import StringListPathField
from awx.conf.tests.unit.test_fields import TestStringListPathField as ShippedTests


class TestStringListPathFieldNoFilesystemOracle:
    """Regression: path validation must not probe the filesystem.

    Before the fix, StringListPathField.to_internal_value used
    os.path.exists() to validate paths, creating a boolean oracle that
    leaked whether arbitrary absolute paths existed on disk.  The fix
    replaced that check with str.startswith('/') so that any absolute
    path is accepted regardless of filesystem state, and only
    non-absolute paths are rejected.
    """

    @pytest.mark.parametrize(
        "path, expected",
        [
            ("/nonexistent/venv/path", ["/nonexistent/venv/path"]),
            ("/no/such/directory/anywhere", ["/no/such/directory/anywhere"]),
            (
                "/tmp/absent_012345/child",
                ["/tmp/absent_012345/child"],
            ),
        ],
    )
    def test_nonexistent_absolute_path_accepted(self, path, expected):
        """Absolute paths that do not exist on disk must be accepted."""
        field = StringListPathField()
        result = field.to_internal_value([path])
        assert result == expected

    @pytest.mark.parametrize(
        "path",
        [
            "relative/path",
            "../traversal",
            ".",
            "..",
        ],
    )
    def test_relative_path_still_rejected(self, path):
        """Non-absolute paths must still be rejected."""
        field = StringListPathField()
        with pytest.raises(ValidationError) as exc_info:
            field.to_internal_value([path])
        assert "You must provide an absolute path" in str(exc_info.value.detail[0])

    @pytest.mark.parametrize("value", ShippedTests.FIELD_VALUES_INVALID_PATH)
    def test_shipped_invalid_path_error_message(self, value):
        """Verify shipped invalid-path cases produce the updated message."""
        inst = ShippedTests()
        inst.test_to_internal_value_invalid_path(value)

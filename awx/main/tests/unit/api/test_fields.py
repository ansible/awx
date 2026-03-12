import pytest
from collections import OrderedDict
from unittest import mock

from rest_framework.exceptions import ValidationError

from awx.api.fields import DeprecatedCredentialField


class TestDeprecatedCredentialField:
    """Test that DeprecatedCredentialField handles unexpected input types gracefully."""

    def test_dict_value_raises_validation_error(self):
        """Passing a dict instead of an integer should return a 400 validation error, not a 500 TypeError."""
        field = DeprecatedCredentialField()
        with pytest.raises(ValidationError):
            field.to_internal_value({"username": "admin", "password": "secret"})

    def test_ordered_dict_value_raises_validation_error(self):
        """Passing an OrderedDict should return a 400 validation error, not a 500 TypeError."""
        field = DeprecatedCredentialField()
        with pytest.raises(ValidationError):
            field.to_internal_value(OrderedDict([("username", "admin")]))

    def test_list_value_raises_validation_error(self):
        """Passing a list should return a 400 validation error, not a 500 TypeError."""
        field = DeprecatedCredentialField()
        with pytest.raises(ValidationError):
            field.to_internal_value([1, 2, 3])

    def test_string_value_raises_validation_error(self):
        """Passing a non-numeric string should return a 400 validation error."""
        field = DeprecatedCredentialField()
        with pytest.raises(ValidationError):
            field.to_internal_value("not_a_number")

    @mock.patch('awx.api.fields.Credential.objects')
    def test_valid_integer_value_works(self, mock_cred_objects):
        """Passing a valid integer PK should work when the credential exists."""
        mock_cred_objects.get.return_value = mock.MagicMock()
        field = DeprecatedCredentialField()
        assert field.to_internal_value(42) == 42

    @mock.patch('awx.api.fields.Credential.objects')
    def test_valid_string_integer_value_works(self, mock_cred_objects):
        """Passing a numeric string PK should work when the credential exists."""
        mock_cred_objects.get.return_value = mock.MagicMock()
        field = DeprecatedCredentialField()
        assert field.to_internal_value("42") == 42

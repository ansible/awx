from unittest import mock

import pytest
from rest_framework import serializers

from awx.api.serializers import AdHocCommandSerializer


class TestAdHocCommandSerializerLimitValidation(object):
    """The limit field must not start with a dash to prevent argument injection
    into the ansible CLI (CWE-88)."""

    @mock.patch(
        'awx.api.serializers.UnifiedJobSerializer.validate',
        side_effect=lambda attrs: attrs,
    )
    @pytest.mark.parametrize('limit', ['--version', '-e', '--help'])
    def test_limit_rejects_dash_prefix(self, mock_super_validate, limit):
        serializer = AdHocCommandSerializer()
        with pytest.raises(serializers.ValidationError) as exc_info:
            serializer.validate({'limit': limit})
        assert 'limit' in exc_info.value.detail

    @mock.patch(
        'awx.api.serializers.UnifiedJobSerializer.validate',
        side_effect=lambda attrs: attrs,
    )
    @pytest.mark.parametrize('limit', ['webservers', 'host1:host2', ''])
    def test_limit_allows_normal_values(self, mock_super_validate, limit):
        result = AdHocCommandSerializer().validate({'limit': limit})
        assert result == {'limit': limit}

    @mock.patch(
        'awx.api.serializers.UnifiedJobSerializer.validate',
        side_effect=lambda attrs: attrs,
    )
    def test_limit_allows_absent(self, mock_super_validate):
        result = AdHocCommandSerializer().validate({})
        assert result == {}

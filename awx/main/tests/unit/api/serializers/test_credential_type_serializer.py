# Copyright (c) 2026 Ansible, Inc.
# All Rights Reserved.

from unittest.mock import patch, MagicMock

import pytest
from django.test import override_settings

from awx.api import validation_patterns


FAKE_TIER2_PATTERN = r'^(?!.*<[a-zA-Z/!][^>]*>)[\s\S]*$'


@pytest.fixture
def fake_tier2_pattern(monkeypatch):
    monkeypatch.setattr(validation_patterns, 'build_tier2_frontend_pattern', lambda: FAKE_TIER2_PATTERN)


def _base_representation(fields=None, metadata=None, managed=False):
    """Build a dict that mimics what BaseSerializer.to_representation returns."""
    inputs = {'fields': list(fields or [])}
    if metadata is not None:
        inputs['metadata'] = list(metadata)
    return {
        'id': 1,
        'type': 'credential_type',
        'name': 'Test Type',
        'kind': 'cloud',
        'managed': managed,
        'namespace': None,
        'inputs': inputs,
        'injectors': {},
    }


class TestCredentialTypeSerializerInjectsPatterns:
    @patch('awx.api.serializers.BaseSerializer.to_representation')
    def test_inject_patterns_on_fields_and_metadata(self, mock_super, fake_tier2_pattern):
        mock_super.return_value = _base_representation(
            fields=[
                {'id': 'username', 'label': 'Username', 'type': 'string'},
                {'id': 'token', 'label': 'Token', 'type': 'string', 'secret': True},
            ],
            metadata=[
                {'id': 'key', 'label': 'Key', 'type': 'string'},
            ],
        )

        from awx.api.serializers import CredentialTypeSerializer

        serializer = CredentialTypeSerializer()
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=True):
            result = serializer.to_representation(MagicMock())

        fields = {f['id']: f for f in result['inputs']['fields']}
        assert fields['username'].get('pattern') == FAKE_TIER2_PATTERN
        assert 'pattern_description' in fields['username']
        assert 'pattern' not in fields['token']
        metadata = {f['id']: f for f in result['inputs']['metadata']}
        assert metadata['key'].get('pattern') == FAKE_TIER2_PATTERN

    @patch('awx.api.serializers.BaseSerializer.to_representation')
    def test_inject_patterns_skipped_when_toggle_off(self, mock_super, fake_tier2_pattern):
        mock_super.return_value = _base_representation(
            fields=[{'id': 'username', 'label': 'Username', 'type': 'string'}],
        )

        from awx.api.serializers import CredentialTypeSerializer

        serializer = CredentialTypeSerializer()
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=False):
            result = serializer.to_representation(MagicMock())

        fields = {f['id']: f for f in result['inputs']['fields']}
        assert 'pattern' not in fields['username']

    @patch('awx.api.serializers.BaseSerializer.to_representation')
    def test_inject_patterns_handles_none_metadata(self, mock_super, fake_tier2_pattern):
        mock_super.return_value = _base_representation(
            fields=[{'id': 'host', 'label': 'Host', 'type': 'string'}],
        )

        from awx.api.serializers import CredentialTypeSerializer

        serializer = CredentialTypeSerializer()
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=True):
            result = serializer.to_representation(MagicMock())

        fields = {f['id']: f for f in result['inputs']['fields']}
        assert fields['host'].get('pattern') == FAKE_TIER2_PATTERN
        assert 'metadata' not in result['inputs']

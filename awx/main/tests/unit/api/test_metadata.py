# Copyright (c) 2026 Ansible, Inc.
# All Rights Reserved.

from unittest.mock import MagicMock

from rest_framework import serializers

from awx.api import metadata as awx_metadata


FAKE_TIER2_PATTERN = r'^(?!.*<[a-zA-Z/!][^>]*>)[\s\S]*$'


class PlainSerializer(serializers.Serializer):
    name = serializers.CharField()


class NotificationConfigSerializer(serializers.Serializer):
    notification_configuration = serializers.JSONField()


class TestMetadataGetFieldInfoInjectsTopLevelPatterns:
    def test_calls_inject_top_level_clean_text_patterns(self, monkeypatch):
        calls = []

        def fake_inject(field, field_info):
            calls.append((field, field_info))
            field_info['pattern'] = 'FAKE'
            return field_info

        monkeypatch.setattr(awx_metadata, 'inject_top_level_clean_text_patterns', fake_inject)

        serializer = PlainSerializer()
        field = serializer.fields['name']

        field_info = awx_metadata.Metadata().get_field_info(field)

        assert field_info['pattern'] == 'FAKE'
        assert len(calls) == 1
        assert calls[0][0] is field

    def test_no_op_when_dab_helper_missing(self, monkeypatch):
        # inject_top_level_clean_text_patterns itself no-ops when the DAB helper
        # is unavailable; verify Metadata still returns clean field_info in that case.
        monkeypatch.setattr(awx_metadata, 'inject_top_level_clean_text_patterns', lambda field, field_info: field_info)

        serializer = PlainSerializer()
        field = serializer.fields['name']

        field_info = awx_metadata.Metadata().get_field_info(field)

        assert 'pattern' not in field_info


class TestMetadataNotificationConfigurationInjection:
    def test_calls_inject_patterns_into_init_parameters_for_each_type(self, monkeypatch):
        calls = []

        def tracking_inject(init_params):
            calls.append(init_params)
            return {'host': {'label': 'Host', 'type': 'string', 'pattern': 'FAKE'}}

        monkeypatch.setattr(awx_metadata, 'inject_patterns_into_init_parameters', tracking_inject)
        monkeypatch.setattr(awx_metadata, 'inject_top_level_clean_text_patterns', lambda f, fi: fi)

        mock_backend = MagicMock()
        mock_backend.init_parameters = {'host': {'label': 'Host', 'type': 'string'}}

        fake_types = [('email', 'Email', mock_backend)]
        monkeypatch.setattr(awx_metadata, 'NotificationTemplate', MagicMock(NOTIFICATION_TYPES=fake_types))

        serializer = NotificationConfigSerializer()
        field = serializer.fields['notification_configuration']

        field_info = awx_metadata.Metadata().get_field_info(field)

        assert len(calls) == 1
        assert calls[0] == mock_backend.init_parameters
        assert field_info['email'] == {'host': {'label': 'Host', 'type': 'string', 'pattern': 'FAKE'}}

    def test_injects_patterns_for_multiple_notification_types(self, monkeypatch):
        call_count = []

        def counting_inject(init_params):
            call_count.append(1)
            return dict(init_params)

        monkeypatch.setattr(awx_metadata, 'inject_patterns_into_init_parameters', counting_inject)
        monkeypatch.setattr(awx_metadata, 'inject_top_level_clean_text_patterns', lambda f, fi: fi)

        mock_email = MagicMock()
        mock_email.init_parameters = {'host': {'label': 'Host', 'type': 'string'}}
        mock_slack = MagicMock()
        mock_slack.init_parameters = {'token': {'label': 'Token', 'type': 'password'}}

        fake_types = [('email', 'Email', mock_email), ('slack', 'Slack', mock_slack)]
        monkeypatch.setattr(awx_metadata, 'NotificationTemplate', MagicMock(NOTIFICATION_TYPES=fake_types))

        serializer = NotificationConfigSerializer()
        field = serializer.fields['notification_configuration']

        field_info = awx_metadata.Metadata().get_field_info(field)

        assert len(call_count) == 2
        assert 'email' in field_info
        assert 'slack' in field_info

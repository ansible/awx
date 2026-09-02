# Copyright (c) 2026 Ansible, Inc.
# All Rights Reserved.

import pytest
from django.test import override_settings

from awx.api import validation_patterns
from awx.main.notifications.email_backend import CustomEmailBackend


FAKE_PATTERN = r'^(?!.*<[a-zA-Z/!][^>]*>)[\s\S]*$'


@pytest.fixture
def fake_tier2_pattern(monkeypatch):
    monkeypatch.setattr(validation_patterns, 'build_tier2_frontend_pattern', lambda: FAKE_PATTERN)


class TestEnhancedInputValidationEnabled:
    def test_off_by_default(self):
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=False):
            assert validation_patterns.enhanced_input_validation_enabled() is False

    def test_on_when_setting_true(self):
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=True):
            assert validation_patterns.enhanced_input_validation_enabled() is True


class TestInjectFreeTextPattern:
    def test_no_op_when_toggle_off(self, fake_tier2_pattern):
        schema = {'id': 'username', 'label': 'Username', 'type': 'string'}
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=False):
            validation_patterns.inject_free_text_pattern(schema)
        assert 'pattern' not in schema
        assert 'pattern_description' not in schema

    def test_injects_tier2_when_toggle_on(self, fake_tier2_pattern):
        schema = {'id': 'username', 'label': 'Username', 'type': 'string'}
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=True):
            validation_patterns.inject_free_text_pattern(schema)
        assert schema['pattern'] == FAKE_PATTERN
        assert schema['pattern_description'] == validation_patterns.TIER2_PATTERN_DESCRIPTION
        assert schema['flags'] == 'i'

    def test_skips_secret_fields(self, fake_tier2_pattern):
        schema = {'id': 'password', 'label': 'Password', 'type': 'string', 'secret': True}
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=True):
            validation_patterns.inject_free_text_pattern(schema)
        assert 'pattern' not in schema

    def test_skips_non_string_fields(self, fake_tier2_pattern):
        schema = {'id': 'port', 'label': 'Port', 'type': 'int'}
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=True):
            validation_patterns.inject_free_text_pattern(schema)
        assert 'pattern' not in schema

    def test_treats_missing_type_as_string(self, fake_tier2_pattern):
        schema = {'id': 'host', 'label': 'Host'}
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=True):
            validation_patterns.inject_free_text_pattern(schema)
        assert schema['pattern'] == FAKE_PATTERN

    def test_no_op_when_dab_helper_missing(self, monkeypatch):
        monkeypatch.setattr(validation_patterns, 'build_tier2_frontend_pattern', None)
        schema = {'id': 'username', 'type': 'string'}
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=True):
            validation_patterns.inject_free_text_pattern(schema)
        assert 'pattern' not in schema

    def test_ignores_non_dict(self, fake_tier2_pattern):
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=True):
            assert validation_patterns.inject_free_text_pattern('not-a-dict') == 'not-a-dict'


class TestInjectPatternsIntoFieldList:
    def test_injects_only_non_secret_strings(self, fake_tier2_pattern):
        fields = [
            {'id': 'username', 'type': 'string'},
            {'id': 'password', 'type': 'string', 'secret': True},
            {'id': 'verify_ssl', 'type': 'boolean'},
        ]
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=True):
            validation_patterns.inject_patterns_into_field_list(fields)
        assert 'pattern' in fields[0]
        assert 'pattern' not in fields[1]
        assert 'pattern' not in fields[2]

    def test_returns_non_list_unchanged(self, fake_tier2_pattern):
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=True):
            assert validation_patterns.inject_patterns_into_field_list('not-a-list') == 'not-a-list'


class TestInjectPatternsIntoInitParameters:
    def test_does_not_mutate_class_level_dict(self, fake_tier2_pattern):
        original = CustomEmailBackend.init_parameters
        host_before = dict(original['host'])
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=True):
            injected = validation_patterns.inject_patterns_into_init_parameters(original)
        assert 'pattern' in injected['host']
        assert 'pattern' not in original['host']
        assert original['host'] == host_before

    def test_skips_password_and_non_string_types(self, fake_tier2_pattern):
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=True):
            injected = validation_patterns.inject_patterns_into_init_parameters(CustomEmailBackend.init_parameters)
        assert 'pattern' in injected['host']
        assert 'pattern' in injected['username']
        assert 'pattern' in injected['sender']
        assert 'pattern' not in injected['password']
        assert 'pattern' not in injected['port']
        assert 'pattern' not in injected['use_tls']
        assert 'pattern' not in injected['recipients']

    def test_toggle_off_returns_copy_without_patterns(self, fake_tier2_pattern):
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=False):
            injected = validation_patterns.inject_patterns_into_init_parameters(CustomEmailBackend.init_parameters)
        assert 'pattern' not in injected['host']
        assert injected['host'] == CustomEmailBackend.init_parameters['host']
        assert injected is not CustomEmailBackend.init_parameters

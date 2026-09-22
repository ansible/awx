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


class TestFreeTextPatternMetadata:
    def test_returns_pattern_dict_when_helper_available(self, fake_tier2_pattern):
        result = validation_patterns.free_text_pattern_metadata()
        assert result is not None
        assert result['pattern'] == FAKE_PATTERN
        assert result['pattern_description'] == validation_patterns.TIER2_PATTERN_DESCRIPTION
        assert result['flags'] == 'i'

    def test_returns_none_when_helper_missing(self, monkeypatch):
        monkeypatch.setattr(validation_patterns, 'build_tier2_frontend_pattern', None)
        assert validation_patterns.free_text_pattern_metadata() is None


class TestIsStringSchema:
    def test_string_type_in_schema(self):
        assert validation_patterns._is_string_schema({'type': 'string'}) is True

    def test_str_type_in_schema(self):
        assert validation_patterns._is_string_schema({'type': 'str'}) is True

    def test_non_string_type_in_schema(self):
        assert validation_patterns._is_string_schema({'type': 'boolean'}) is False

    def test_missing_type_defaults_to_string(self):
        assert validation_patterns._is_string_schema({}) is True

    def test_explicit_field_type_overrides_schema(self):
        assert validation_patterns._is_string_schema({'type': 'boolean'}, field_type='string') is True
        assert validation_patterns._is_string_schema({'type': 'string'}, field_type='int') is False


class TestInjectFreeTextPatternSecretKwarg:
    def test_skips_when_secret_kwarg_true(self, fake_tier2_pattern):
        schema = {'id': 'token', 'type': 'string'}
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=True):
            validation_patterns.inject_free_text_pattern(schema, secret=True)
        assert 'pattern' not in schema

    def test_injects_when_secret_kwarg_false(self, fake_tier2_pattern):
        schema = {'id': 'host', 'type': 'string'}
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=True):
            validation_patterns.inject_free_text_pattern(schema, secret=False)
        assert schema['pattern'] == FAKE_PATTERN


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

    def test_ignores_non_list(self, fake_tier2_pattern):
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=True):
            assert validation_patterns.inject_patterns_into_field_list('not-a-list') is None

    def test_handles_none_input(self, fake_tier2_pattern):
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=True):
            assert validation_patterns.inject_patterns_into_field_list(None) is None

    def test_handles_empty_list(self, fake_tier2_pattern):
        fields = []
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=True):
            validation_patterns.inject_patterns_into_field_list(fields)
        assert fields == []


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

    def test_non_dict_input_returns_empty_dict(self, fake_tier2_pattern):
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=True):
            result = validation_patterns.inject_patterns_into_init_parameters('not-a-dict')
        assert result == {}

    def test_none_input_returns_empty_dict(self, fake_tier2_pattern):
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=True):
            result = validation_patterns.inject_patterns_into_init_parameters(None)
        assert result == {}

    def test_list_input_returns_empty_dict(self, fake_tier2_pattern):
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=True):
            result = validation_patterns.inject_patterns_into_init_parameters([1, 2, 3])
        assert result == {}

    def test_skips_non_dict_values(self, fake_tier2_pattern):
        params = {
            'host': {'label': 'Host', 'type': 'string'},
            'extra_info': 'just-a-string',
            'count': 42,
        }
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=True):
            result = validation_patterns.inject_patterns_into_init_parameters(params)
        assert 'pattern' in result['host']
        assert result['extra_info'] == 'just-a-string'
        assert result['count'] == 42

    def test_non_dict_input_toggle_off_returns_empty_dict(self, fake_tier2_pattern):
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=False):
            result = validation_patterns.inject_patterns_into_init_parameters(None)
        assert result == {}

    def test_empty_dict_returns_empty_dict(self, fake_tier2_pattern):
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=True):
            result = validation_patterns.inject_patterns_into_init_parameters({})
        assert result == {}


class TestInjectTopLevelCleanTextPatterns:
    def test_no_op_when_dab_helper_missing(self, monkeypatch):
        monkeypatch.setattr(validation_patterns, '_dab_inject_clean_text_patterns', None)
        field_info = {'type': 'string'}
        result = validation_patterns.inject_top_level_clean_text_patterns(object(), field_info)
        assert result == {'type': 'string'}

    def test_delegates_to_dab_helper(self, monkeypatch):
        calls = []

        def fake_dab_inject(field, field_info):
            calls.append((field, field_info))
            field_info['pattern'] = 'FAKE'
            return field_info

        monkeypatch.setattr(validation_patterns, '_dab_inject_clean_text_patterns', fake_dab_inject)
        sentinel_field = object()
        field_info = {'type': 'string'}

        result = validation_patterns.inject_top_level_clean_text_patterns(sentinel_field, field_info)

        assert result['pattern'] == 'FAKE'
        assert calls == [(sentinel_field, field_info)]

    def test_plain_serializer_fake_meta_gets_tier2(self, monkeypatch):
        from ansible_base.lib.serializers.mixins import CleanTextMixin
        from rest_framework import serializers as drf_serializers

        monkeypatch.setattr(validation_patterns, '_get_tier1_pattern', lambda: {'pattern': 'T1', 'description': 'd1', 'flags': 'u', 'normalize': 'NFC'})
        monkeypatch.setattr(validation_patterns, '_get_tier2_pattern', lambda: {'pattern': 'T2', 'description': 'd2', 'flags': 'i'})

        class FakeOpts:
            app_label = 'conf'
            object_name = 'SettingSingleton'

        class FakeModel:
            _meta = FakeOpts()

        class PlainCleanText(CleanTextMixin, drf_serializers.Serializer):
            class Meta:
                model = FakeModel

            excluded_fields = frozenset()
            name_fields = frozenset({'name'})

        serializer = PlainCleanText()
        field = drf_serializers.CharField()
        field.bind('FOO_BAR', serializer)
        field_info = {'type': 'string'}

        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=True):
            result = validation_patterns.inject_top_level_clean_text_patterns(field, field_info)

        assert result['pattern'] == 'T2'
        assert result['patternDescription'] == 'd2'
        assert result['flags'] == 'i'

    def test_plain_serializer_name_field_gets_tier1(self, monkeypatch):
        from ansible_base.lib.serializers.mixins import CleanTextMixin
        from rest_framework import serializers as drf_serializers

        monkeypatch.setattr(validation_patterns, '_get_tier1_pattern', lambda: {'pattern': 'T1', 'description': 'd1', 'flags': 'u', 'normalize': 'NFC'})
        monkeypatch.setattr(validation_patterns, '_get_tier2_pattern', lambda: {'pattern': 'T2', 'description': 'd2', 'flags': 'i'})

        class FakeOpts:
            app_label = 'main'
            object_name = 'CopySerializer'

        class FakeModel:
            _meta = FakeOpts()

        class PlainCleanText(CleanTextMixin, drf_serializers.Serializer):
            class Meta:
                model = FakeModel

            excluded_fields = frozenset()
            name_fields = frozenset({'name'})

        serializer = PlainCleanText()
        field = drf_serializers.CharField()
        field.bind('name', serializer)
        field_info = {'type': 'string'}

        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=True):
            result = validation_patterns.inject_top_level_clean_text_patterns(field, field_info)

        assert result['pattern'] == 'T1'
        assert result['patternDescription'] == 'd1'
        assert result['flags'] == 'u'
        assert result['normalize'] == 'NFC'

    def test_plain_serializer_skips_excluded_fields(self, monkeypatch):
        from ansible_base.lib.serializers.mixins import CleanTextMixin
        from rest_framework import serializers as drf_serializers

        monkeypatch.setattr(validation_patterns, '_get_tier2_pattern', lambda: {'pattern': 'T2', 'description': 'd2', 'flags': 'i'})

        class FakeOpts:
            app_label = 'conf'
            object_name = 'SettingSingleton'

        class FakeModel:
            _meta = FakeOpts()

        class PlainCleanText(CleanTextMixin, drf_serializers.Serializer):
            class Meta:
                model = FakeModel

            excluded_fields = frozenset({'CUSTOM_LOGIN_INFO'})
            name_fields = frozenset()

        serializer = PlainCleanText()
        field = drf_serializers.CharField()
        field.bind('CUSTOM_LOGIN_INFO', serializer)
        field_info = {'type': 'string'}

        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=True):
            result = validation_patterns.inject_top_level_clean_text_patterns(field, field_info)

        assert 'pattern' not in result

    def test_plain_serializer_does_not_call_dab_inject(self, monkeypatch):
        from ansible_base.lib.serializers.mixins import CleanTextMixin
        from rest_framework import serializers as drf_serializers

        called = []

        def boom(field, field_info):
            called.append(True)
            raise AttributeError('should not reach DAB inject')

        monkeypatch.setattr(validation_patterns, '_dab_inject_clean_text_patterns', boom)
        monkeypatch.setattr(validation_patterns, '_get_tier2_pattern', lambda: {'pattern': 'T2', 'description': 'd2', 'flags': 'i'})
        monkeypatch.setattr(validation_patterns, '_get_tier1_pattern', lambda: {'pattern': 'T1', 'description': 'd1', 'flags': 'u', 'normalize': 'NFC'})

        class FakeOpts:
            app_label = 'conf'
            object_name = 'SettingSingleton'

        class FakeModel:
            _meta = FakeOpts()

        class PlainCleanText(CleanTextMixin, drf_serializers.Serializer):
            class Meta:
                model = FakeModel

            excluded_fields = frozenset()
            name_fields = frozenset()

        serializer = PlainCleanText()
        field = drf_serializers.CharField()
        field.bind('FOO', serializer)

        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=True):
            result = validation_patterns.inject_top_level_clean_text_patterns(field, {'type': 'string'})

        assert called == []
        assert result['pattern'] == 'T2'


class TestBuildSurveySpecOptionsSchema:
    def test_injects_patterns_when_toggle_on(self, fake_tier2_pattern):
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=True):
            schema = validation_patterns.build_survey_spec_options_schema()
        assert schema['name']['pattern'] == FAKE_PATTERN
        assert schema['name']['pattern_description'] == validation_patterns.TIER2_PATTERN_DESCRIPTION
        assert schema['description']['pattern'] == FAKE_PATTERN
        assert schema['spec']['type'] == 'json'
        assert schema['spec']['question_name']['pattern'] == FAKE_PATTERN
        assert schema['spec']['question_description']['pattern'] == FAKE_PATTERN
        assert schema['spec']['variable']['pattern'] == FAKE_PATTERN
        assert 'default' not in schema['spec']
        assert 'choices' not in schema['spec']

    def test_omits_patterns_when_toggle_off(self, fake_tier2_pattern):
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=False):
            schema = validation_patterns.build_survey_spec_options_schema()
        assert 'pattern' not in schema['name']
        assert 'pattern' not in schema['description']
        assert 'pattern' not in schema['spec']['question_name']
        assert schema['spec']['variable']['type'] == 'string'


def _survey_payload(**overrides):
    question = {
        'question_name': 'Question',
        'question_description': 'Help',
        'variable': 'my_var',
        'type': 'text',
        'required': True,
    }
    question.update(overrides.pop('question', {}))
    payload = {'name': 'Survey', 'description': 'Desc', 'spec': [question]}
    payload.update(overrides)
    return payload


class TestCollectSurveySpecTextErrors:
    def test_no_op_when_toggle_off(self):
        payload = _survey_payload(question={'question_name': '<script>x</script>'})
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=False):
            assert validation_patterns.collect_survey_spec_text_errors(payload) is None

    def test_rejects_markup_in_editor_strings(self):
        if validation_patterns._validate_free_text is None:
            pytest.skip('DAB validate_free_text is unavailable')
        payload = _survey_payload(question={'question_name': '<script>x</script>'})
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=True):
            errors = validation_patterns.collect_survey_spec_text_errors(payload)
        assert errors is not None
        assert 'spec[0].question_name' in errors

    def test_rejects_top_level_name(self):
        if validation_patterns._validate_free_text is None:
            pytest.skip('DAB validate_free_text is unavailable')
        payload = _survey_payload()
        payload['name'] = '<b>bad</b>'
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=True):
            errors = validation_patterns.collect_survey_spec_text_errors(payload)
        assert errors is not None
        assert 'name' in errors

    def test_skips_default_and_choices(self):
        if validation_patterns._validate_free_text is None:
            pytest.skip('DAB validate_free_text is unavailable')
        payload = _survey_payload(question={'default': '<script>x</script>', 'choices': '{{ foo }}'})
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=True):
            assert validation_patterns.collect_survey_spec_text_errors(payload) is None

    def test_grandfathers_unchanged_invalid_values(self):
        if validation_patterns._validate_free_text is None:
            pytest.skip('DAB validate_free_text is unavailable')
        old = _survey_payload(question={'question_name': '<script>old</script>'})
        new = _survey_payload(question={'question_name': '<script>old</script>', 'question_description': 'updated'})
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=True):
            assert validation_patterns.collect_survey_spec_text_errors(new, old) is None

    def test_validates_changed_question_name_against_legacy_sibling(self):
        if validation_patterns._validate_free_text is None:
            pytest.skip('DAB validate_free_text is unavailable')
        old = _survey_payload(question={'question_name': '<script>old</script>'})
        new = _survey_payload(question={'question_name': '<script>new</script>'})
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=True):
            errors = validation_patterns.collect_survey_spec_text_errors(new, old)
        assert errors is not None
        assert 'spec[0].question_name' in errors

    def test_ignores_non_dict_payload(self):
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=True):
            assert validation_patterns.collect_survey_spec_text_errors('not-a-dict') is None

    def test_no_op_when_validator_missing(self, monkeypatch):
        monkeypatch.setattr(validation_patterns, '_validate_free_text', None)
        payload = _survey_payload(question={'question_name': '<script>x</script>'})
        with override_settings(ENHANCED_INPUT_VALIDATION_ENABLED=True):
            assert validation_patterns.collect_survey_spec_text_errors(payload) is None

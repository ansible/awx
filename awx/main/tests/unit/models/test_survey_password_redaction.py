# -*- coding: utf-8 -*-
import pytest

from awx.main.models import JobTemplate


@pytest.mark.survey
class TestSurveyPasswordRedactionInErrors:
    """Verify that _survey_element_validation never leaks a password-type
    survey answer into its error messages (uses $encrypted$ instead)."""

    @staticmethod
    def _make_element(variable, qtype, **overrides):
        element = {
            'variable': variable,
            'type': qtype,
            'required': True,
            'question_name': variable,
            'question_description': '',
            'choices': '',
            'min': '',
            'max': '',
            'default': '',
        }
        element.update(overrides)
        return element

    # ---- password type: value must NEVER appear in errors ----

    def test_password_non_string_error_is_redacted(self):
        """When a non-string value is submitted for a password field, the
        error message must show $encrypted$ instead of the raw value."""
        element = self._make_element('dbpw', 'password')
        jt = JobTemplate(name='test-jt')
        # Non-string value triggers the type-check branch
        errors = jt._survey_element_validation(element, {'dbpw': 12345})
        assert len(errors) == 1
        assert '$encrypted$' in errors[0]
        assert '12345' not in errors[0]

    def test_password_too_short_error_is_redacted(self):
        """When a password value is shorter than the minimum, the error
        message must show $encrypted$ instead of the raw value."""
        secret = 'ab'
        element = self._make_element('dbpw', 'password', min=5, max=100)
        jt = JobTemplate(name='test-jt')
        errors = jt._survey_element_validation(element, {'dbpw': secret})
        assert len(errors) == 1
        assert '$encrypted$' in errors[0]
        assert secret not in errors[0]

    def test_password_too_long_error_is_redacted(self):
        """When a password value exceeds the maximum length, the error
        message must show $encrypted$ instead of the raw value."""
        secret = 'ThisPasswordIsWayTooLong'
        element = self._make_element('dbpw', 'password', min=0, max=5)
        jt = JobTemplate(name='test-jt')
        errors = jt._survey_element_validation(element, {'dbpw': secret})
        assert len(errors) == 1
        assert '$encrypted$' in errors[0]
        assert secret not in errors[0]

    # ---- text type: value SHOULD still appear in errors (unchanged) ----

    def test_text_non_string_error_shows_value(self):
        """For text-type fields, the raw value should still appear in the
        error message (only passwords are redacted)."""
        element = self._make_element('username', 'text')
        jt = JobTemplate(name='test-jt')
        errors = jt._survey_element_validation(element, {'username': 12345})
        assert len(errors) == 1
        assert '12345' in errors[0]

    def test_text_too_short_error_shows_value(self):
        """For text-type fields, a too-short value should appear in the
        error message as-is."""
        value = 'ab'
        element = self._make_element('username', 'text', min=5, max=100)
        jt = JobTemplate(name='test-jt')
        errors = jt._survey_element_validation(element, {'username': value})
        assert len(errors) == 1
        assert value in errors[0]

    def test_text_too_long_error_shows_value(self):
        """For text-type fields, a too-long value should appear in the
        error message as-is."""
        value = 'ThisValueIsWayTooLong'
        element = self._make_element('username', 'text', min=0, max=5)
        jt = JobTemplate(name='test-jt')
        errors = jt._survey_element_validation(element, {'username': value})
        assert len(errors) == 1
        assert value in errors[0]

    # ---- permit direction: valid inputs still pass ----

    def test_password_valid_value_passes(self):
        """A valid password value within length bounds must produce no
        errors — the guard must not over-reject."""
        element = self._make_element('dbpw', 'password', min=3, max=20)
        jt = JobTemplate(name='test-jt')
        errors = jt._survey_element_validation(element, {'dbpw': 'GoodPassword1'})
        assert errors == []

    def test_text_valid_value_passes(self):
        """A valid text value within length bounds must produce no errors."""
        element = self._make_element('username', 'text', min=3, max=20)
        jt = JobTemplate(name='test-jt')
        errors = jt._survey_element_validation(element, {'username': 'validuser'})
        assert errors == []

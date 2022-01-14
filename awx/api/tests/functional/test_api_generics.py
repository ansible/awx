import pytest

# We have to tell flake 8 to ignore these since they are fixtures we need to import
from awx.conf.tests.functional.conftest import api_request, admin  # noqa: F401; pylint: disable=unused-variable


@pytest.mark.django_db
def test_change_400_error_log(caplog, api_request, settings):
    settings.API_400_ERROR_LOG_FORMAT = 'Test'
    api_request('post', '/api/v2/settings/logging/test/')
    assert 'Test' in caplog.text


@pytest.mark.django_db
def test_bad_400_error_log(caplog, api_request, settings):
    settings.API_400_ERROR_LOG_FORMAT = "Not good {junk}"
    api_request('post', '/api/v2/settings/logging/test/')
    assert 'Unable to format API_400_ERROR_LOG_FORMAT setting, defaulting log message' in caplog.text
    assert 'status 409 received by user conf-admin attempting to access /api/v2/settings/logging/test/ from 127.0.0.1' in caplog.text


@pytest.mark.django_db
def test_custom_400_error_log(caplog, api_request, settings):
    settings.API_400_ERROR_LOG_FORMAT = "{status_code} {error}"
    api_request('post', '/api/v2/settings/logging/test/')
    assert '409 Logging not enabled' in caplog.text

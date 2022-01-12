import pytest

from awx.conf.tests.functional.conftest import api_request, admin


@pytest.mark.django_db
def test_change_400_error_log(caplog, api_request, settings):
    settings.API_400_ERROR_LOG_FORMAT = 'Test'
    response = api_request('post', '/api/v2/settings/logging/test/')
    assert 'Test' in caplog.text


@pytest.mark.django_db
def test_bad_400_error_log(caplog, api_request, settings):
    settings.API_400_ERROR_LOG_FORMAT = "Not good {junk}"
    response = api_request('post', '/api/v2/settings/logging/test/')
    assert 'Unable to format API_400_ERROR_LOG_FORMAT setting, defaulting log message' in caplog.text
    assert 'status 409 received by user conf-admin attempting to access /api/v2/settings/logging/test/ from 127.0.0.1' in caplog.text


@pytest.mark.django_db
def test_custom_400_error_log(caplog, api_request, settings):
    settings.API_400_ERROR_LOG_FORMAT = "{status_code} {error}"
    response = api_request('post', '/api/v2/settings/logging/test/')
    assert '409 Logging not enabled' in caplog.text

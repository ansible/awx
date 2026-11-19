import pytest

from django.test.utils import override_settings
from awx.api.versioning import reverse


@pytest.mark.django_db
def test_change_400_error_log(caplog, post, admin_user):
    with override_settings(API_400_ERROR_LOG_FORMAT='Test'):
        post(url=reverse('api:setting_logging_test'), data={}, user=admin_user, expect=409)
        assert 'Test' in caplog.text


@pytest.mark.django_db
def test_bad_400_error_log(caplog, post, admin_user):
    with override_settings(API_400_ERROR_LOG_FORMAT="Not good {junk}"):
        post(url=reverse('api:setting_logging_test'), data={}, user=admin_user, expect=409)
        assert "Unable to format API_400_ERROR_LOG_FORMAT setting, defaulting log message: 'junk'" in caplog.text
        assert 'status 409 received by user admin attempting to access /api/v2/settings/logging/test/ from 127.0.0.1' in caplog.text


@pytest.mark.django_db
def test_custom_400_error_log(caplog, post, admin_user):
    with override_settings(API_400_ERROR_LOG_FORMAT="{status_code} {error}"):
        post(url=reverse('api:setting_logging_test'), data={}, user=admin_user, expect=409)
        assert '409 Logging not enabled' in caplog.text


# The above tests the generation function with a dict/object.
# The tower-qa test tests.api.inventories.test_inventory_update.TestInventoryUpdate.test_update_all_inventory_sources_with_nonfunctional_sources tests the function with a list
# Someday it would be nice to test the else condition (not a dict/list) but we need to find an API test which will do this. For now it was added just as a catch all


@pytest.mark.django_db
def test_user_name_format_string_traversal_blocked(caplog, post, admin_user):
    """The user_name value in msg_data must be a plain string so that
    Python's str.format() cannot traverse model attributes.  Before the
    fix, user_name was the raw User object and format specifiers like
    {user_name.__class__.__name__} resolved to 'User'; after the fix it
    resolves to 'str'."""
    fmt = '{user_name.__class__.__name__}'
    with override_settings(API_400_ERROR_LOG_FORMAT=fmt):
        post(url=reverse('api:setting_logging_test'), data={}, user=admin_user, expect=409)
        assert 'str' in caplog.text
        assert 'User' not in caplog.text


@pytest.mark.django_db
def test_user_name_still_logged_correctly(caplog, post, admin_user):
    """Normal {user_name} formatting must still produce the username string
    so that legitimate log messages are not broken by the str() wrapping."""
    fmt = 'user={user_name}'
    with override_settings(API_400_ERROR_LOG_FORMAT=fmt):
        post(url=reverse('api:setting_logging_test'), data={}, user=admin_user, expect=409)
        assert 'user=admin' in caplog.text

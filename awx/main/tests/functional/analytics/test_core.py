import importlib
import json
import os
import tarfile
import tempfile
from unittest import mock
import pytest

from django.conf import settings
from django.test.utils import override_settings
from awx.main.analytics import gather, register, ship


@register('example', '1.0')
def example(since, **kwargs):
    return {'awx': 123}


@register('bad_json', '1.0')
def bad_json(since, **kwargs):
    return set()


@register('throws_error', '1.0')
def throws_error(since, **kwargs):
    raise ValueError()


def _valid_license():
    pass


@pytest.fixture
def mock_valid_license():
    with mock.patch('awx.main.analytics.core._valid_license') as license:
        license.return_value = True
        yield license


@pytest.mark.django_db
def test_gather(mock_valid_license):
    settings.INSIGHTS_TRACKING_STATE = True

    tgzfiles = gather(module=importlib.import_module(__name__), collection_type='dry-run')
    files = {}
    with tarfile.open(tgzfiles[0], "r:gz") as archive:
        for member in archive.getmembers():
            files[member.name] = archive.extractfile(member)

        # functions that returned valid JSON should show up
        assert './example.json' in files.keys()
        assert json.loads(files['./example.json'].read()) == {'awx': 123}

        # functions that don't return serializable objects should not
        assert './bad_json.json' not in files.keys()
        assert './throws_error.json' not in files.keys()
    try:
        for tgz in tgzfiles:
            os.remove(tgz)
    except Exception:
        pass


@pytest.fixture
def temp_analytic_tar():
    # Create a temporary file and yield its path
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(b"data")
        temp_file_path = temp_file.name
    yield temp_file_path
    # Clean up the temporary file after the test
    os.remove(temp_file_path)


@pytest.fixture
def mock_analytic_post():
    # Patch get_or_generate_candlepin_certificate to skip mTLS path
    with mock.patch('awx.main.analytics.core.get_or_generate_candlepin_certificate', return_value=(None, None)):
        yield


@pytest.mark.parametrize(
    "setting_map, expected_result, expected_auth",
    [
        # Valid Red Hat credentials
        (
            {
                'REDHAT_USERNAME': 'redhat_user',
                'REDHAT_PASSWORD': 'redhat_pass',  # NOSONAR
                'SUBSCRIPTIONS_CLIENT_ID': '',
                'SUBSCRIPTIONS_CLIENT_SECRET': '',
            },
            True,
            ('redhat_user', 'redhat_pass'),
        ),
        # Valid Subscription credentials with no Red Hat credentials
        (
            {
                'REDHAT_USERNAME': None,
                'REDHAT_PASSWORD': None,
                'SUBSCRIPTIONS_CLIENT_ID': 'subs_user',
                'SUBSCRIPTIONS_CLIENT_SECRET': 'subs_pass',  # NOSONAR
            },
            True,
            ('subs_user', 'subs_pass'),
        ),
        # Valid Subscription credentials with empty Red Hat credentials
        (
            {
                'REDHAT_USERNAME': '',
                'REDHAT_PASSWORD': '',
                'SUBSCRIPTIONS_CLIENT_ID': 'subs_user',
                'SUBSCRIPTIONS_CLIENT_SECRET': 'subs_pass',  # NOSONAR
            },
            True,
            ('subs_user', 'subs_pass'),
        ),
        # No credentials
        (
            {
                'REDHAT_USERNAME': '',
                'REDHAT_PASSWORD': '',
                'SUBSCRIPTIONS_CLIENT_ID': '',
                'SUBSCRIPTIONS_CLIENT_SECRET': '',
            },
            False,
            None,  # No request should be made
        ),
        # Mixed credentials
        (
            {
                'REDHAT_USERNAME': '',
                'REDHAT_PASSWORD': 'redhat_pass',  # NOSONAR
                'SUBSCRIPTIONS_CLIENT_ID': 'subs_user',
                'SUBSCRIPTIONS_CLIENT_SECRET': '',
            },
            False,
            None,  # Invalid, no request should be made
        ),
    ],
)
@pytest.mark.django_db
def test_ship_credential(setting_map, expected_result, expected_auth, temp_analytic_tar, mock_analytic_post):
    with override_settings(**setting_map, AUTOMATION_ANALYTICS_URL='https://example.com/api'):
        with mock.patch('awx.main.analytics.core.OIDCClient') as mock_oidc:
            mock_oidc_instance = mock.Mock()
            mock_oidc_instance.make_request.return_value = mock.Mock(status_code=200)
            mock_oidc.return_value = mock_oidc_instance

            result = ship(temp_analytic_tar)

            assert result == expected_result
            if expected_auth:
                # Verify OIDC client was instantiated with correct credentials
                mock_oidc.assert_called_once_with(expected_auth[0], expected_auth[1])
                mock_oidc_instance.make_request.assert_called_once()
            else:
                # When credentials are missing, OIDCClient should not be called
                mock_oidc.assert_not_called()


@pytest.mark.django_db
def test_gather_cleanup_on_auth_failure(mock_valid_license, temp_analytic_tar):
    settings.INSIGHTS_TRACKING_STATE = True
    settings.AUTOMATION_ANALYTICS_URL = 'https://example.com/api'
    settings.REDHAT_USERNAME = 'test_user'
    settings.REDHAT_PASSWORD = 'test_password'

    with tempfile.NamedTemporaryFile(delete=False, suffix='.tar.gz') as temp_file:
        temp_file_path = temp_file.name

    try:
        with mock.patch('awx.main.analytics.core.ship', return_value=False):
            with mock.patch('awx.main.analytics.core.package', return_value=temp_file_path):
                gather(module=importlib.import_module(__name__), collection_type='scheduled')

                assert not os.path.exists(temp_file_path), "Temp file was not cleaned up after ship failure"
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

from unittest import mock
import pytest


def test_empty_host_fails_auth(tacacsplus_backend):
    with mock.patch('awx.sso.backends.django_settings') as settings:
        settings.TACACSPLUS_HOST = ''
        ret_user = tacacsplus_backend.authenticate(None, u"user", u"pass")
        assert ret_user is None


def test_client_raises_exception(tacacsplus_backend):
    client = mock.MagicMock()
    client.authenticate.side_effect = Exception("foo")
    with mock.patch('awx.sso.backends.django_settings') as settings, mock.patch('awx.sso.backends.logger') as logger, mock.patch(
        'tacacs_plus.TACACSClient', return_value=client
    ):
        settings.TACACSPLUS_HOST = 'localhost'
        settings.TACACSPLUS_AUTH_PROTOCOL = 'ascii'
        ret_user = tacacsplus_backend.authenticate(None, u"user", u"pass")
        assert ret_user is None
        logger.exception.assert_called_once_with("TACACS+ Authentication Error: foo")


def test_client_return_invalid_fails_auth(tacacsplus_backend):
    auth = mock.MagicMock()
    auth.valid = False
    client = mock.MagicMock()
    client.authenticate.return_value = auth
    with mock.patch('awx.sso.backends.django_settings') as settings, mock.patch('tacacs_plus.TACACSClient', return_value=client):
        settings.TACACSPLUS_HOST = 'localhost'
        settings.TACACSPLUS_AUTH_PROTOCOL = 'ascii'
        ret_user = tacacsplus_backend.authenticate(None, u"user", u"pass")
        assert ret_user is None


def test_client_return_valid_passes_auth(tacacsplus_backend):
    auth = mock.MagicMock()
    auth.valid = True
    client = mock.MagicMock()
    client.authenticate.return_value = auth
    user = mock.MagicMock()
    user.has_usable_password = mock.MagicMock(return_value=False)
    with mock.patch('awx.sso.backends.django_settings') as settings, mock.patch('tacacs_plus.TACACSClient', return_value=client), mock.patch(
        'awx.sso.backends._get_or_set_enterprise_user', return_value=user
    ):
        settings.TACACSPLUS_HOST = 'localhost'
        settings.TACACSPLUS_AUTH_PROTOCOL = 'ascii'
        ret_user = tacacsplus_backend.authenticate(None, u"user", u"pass")
        assert ret_user == user


@pytest.mark.parametrize(
    "client_ip_header,client_ip_header_value,expected_client_ip",
    [('HTTP_X_FORWARDED_FOR', '12.34.56.78, 23.45.67.89', '12.34.56.78'), ('REMOTE_ADDR', '12.34.56.78', '12.34.56.78')],
)
def test_remote_addr_is_passed_to_client_if_available_and_setting_enabled(tacacsplus_backend, client_ip_header, client_ip_header_value, expected_client_ip):
    auth = mock.MagicMock()
    auth.valid = True
    client = mock.MagicMock()
    client.authenticate.return_value = auth
    user = mock.MagicMock()
    user.has_usable_password = mock.MagicMock(return_value=False)
    request = mock.MagicMock()
    request.META = {
        client_ip_header: client_ip_header_value,
    }
    with mock.patch('awx.sso.backends.django_settings') as settings, mock.patch('tacacs_plus.TACACSClient', return_value=client), mock.patch(
        'awx.sso.backends._get_or_set_enterprise_user', return_value=user
    ):
        settings.TACACSPLUS_HOST = 'localhost'
        settings.TACACSPLUS_AUTH_PROTOCOL = 'ascii'
        settings.TACACSPLUS_REM_ADDR = True
        tacacsplus_backend.authenticate(request, u"user", u"pass")

        client.authenticate.assert_called_once_with('user', 'pass', authen_type=1, rem_addr=expected_client_ip)


def test_remote_addr_is_completely_ignored_in_client_call_if_setting_is_disabled(tacacsplus_backend):
    auth = mock.MagicMock()
    auth.valid = True
    client = mock.MagicMock()
    client.authenticate.return_value = auth
    user = mock.MagicMock()
    user.has_usable_password = mock.MagicMock(return_value=False)
    request = mock.MagicMock()
    request.META = {}
    with mock.patch('awx.sso.backends.django_settings') as settings, mock.patch('tacacs_plus.TACACSClient', return_value=client), mock.patch(
        'awx.sso.backends._get_or_set_enterprise_user', return_value=user
    ):
        settings.TACACSPLUS_HOST = 'localhost'
        settings.TACACSPLUS_AUTH_PROTOCOL = 'ascii'
        settings.TACACSPLUS_REM_ADDR = False
        tacacsplus_backend.authenticate(request, u"user", u"pass")

        client.authenticate.assert_called_once_with('user', 'pass', authen_type=1)


def test_remote_addr_is_completely_ignored_in_client_call_if_unavailable_and_setting_enabled(tacacsplus_backend):
    auth = mock.MagicMock()
    auth.valid = True
    client = mock.MagicMock()
    client.authenticate.return_value = auth
    user = mock.MagicMock()
    user.has_usable_password = mock.MagicMock(return_value=False)
    request = mock.MagicMock()
    request.META = {}
    with mock.patch('awx.sso.backends.django_settings') as settings, mock.patch('tacacs_plus.TACACSClient', return_value=client), mock.patch(
        'awx.sso.backends._get_or_set_enterprise_user', return_value=user
    ):
        settings.TACACSPLUS_HOST = 'localhost'
        settings.TACACSPLUS_AUTH_PROTOCOL = 'ascii'
        settings.TACACSPLUS_REM_ADDR = True
        tacacsplus_backend.authenticate(request, u"user", u"pass")

        client.authenticate.assert_called_once_with('user', 'pass', authen_type=1)

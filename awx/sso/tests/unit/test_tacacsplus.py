from unittest import mock


def test_empty_host_fails_auth(tacacsplus_backend):
    with mock.patch('awx.sso.backends.django_settings') as settings:
        settings.TACACSPLUS_HOST = ''
        ret_user = tacacsplus_backend.authenticate(None, u"user", u"pass")
        assert ret_user is None


def test_client_raises_exception(tacacsplus_backend):
    client = mock.MagicMock()
    client.authenticate.side_effect=Exception("foo")
    with mock.patch('awx.sso.backends.django_settings') as settings,\
            mock.patch('awx.sso.backends.logger') as logger,\
            mock.patch('tacacs_plus.TACACSClient', return_value=client):
        settings.TACACSPLUS_HOST = 'localhost'
        settings.TACACSPLUS_AUTH_PROTOCOL = 'ascii'
        ret_user = tacacsplus_backend.authenticate(None, u"user", u"pass")
        assert ret_user is None
        logger.exception.assert_called_once_with(
            "TACACS+ Authentication Error: foo"
        )


def test_client_return_invalid_fails_auth(tacacsplus_backend):
    auth = mock.MagicMock()
    auth.valid = False
    client = mock.MagicMock()
    client.authenticate.return_value = auth
    with mock.patch('awx.sso.backends.django_settings') as settings,\
            mock.patch('tacacs_plus.TACACSClient', return_value=client):
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
    with mock.patch('awx.sso.backends.django_settings') as settings,\
            mock.patch('tacacs_plus.TACACSClient', return_value=client),\
            mock.patch('awx.sso.backends._get_or_set_enterprise_user', return_value=user):
        settings.TACACSPLUS_HOST = 'localhost'
        settings.TACACSPLUS_AUTH_PROTOCOL = 'ascii'
        ret_user = tacacsplus_backend.authenticate(None, u"user", u"pass")
        assert ret_user == user

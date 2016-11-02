from split_settings.tools import include

def test_postprocess_auth_basic_enabled():
    locals().update({'__file__': __file__})

    include('../../../settings/defaults.py', scope=locals())
    assert 'awx.api.authentication.LoggedBasicAuthentication' in locals()['REST_FRAMEWORK']['DEFAULT_AUTHENTICATION_CLASSES']

    locals().update({'AUTH_BASIC_ENABLED': False})
    include('../../../settings/postprocess.py', scope=locals())
    assert 'awx.api.authentication.LoggedBasicAuthentication' not in locals()['REST_FRAMEWORK']['DEFAULT_AUTHENTICATION_CLASSES']

from split_settings.tools import include


LOCAL_SETTINGS = (
    'ALLOWED_HOSTS',
    'BROADCAST_WEBSOCKET_PORT',
    'BROADCAST_WEBSOCKET_VERIFY_CERT',
    'BROADCAST_WEBSOCKET_PROTOCOL',
    'BROADCAST_WEBSOCKET_SECRET',
    'DATABASES',
    'DEBUG',
    'NAMED_URL_GRAPH',
)


def test_postprocess_auth_basic_enabled():
    locals().update({'__file__': __file__})

    include('../../../settings/defaults.py', scope=locals())
    assert 'awx.api.authentication.LoggedBasicAuthentication' in locals()['REST_FRAMEWORK']['DEFAULT_AUTHENTICATION_CLASSES']


def test_default_settings():
    from django.conf import settings

    for k in dir(settings):
        default_val = getattr(settings.default_settings, k, None)
        if k not in settings.DEFAULTS_SNAPSHOT or k in LOCAL_SETTINGS:
            continue
        snapshot_val = settings.DEFAULTS_SNAPSHOT[k]
        if default_val != snapshot_val:
            raise Exception(f'Setting for {k} does not match shapshot:\nsnapshot: {snapshot_val}\ndefault: {default_val}')

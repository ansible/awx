LOCAL_SETTINGS = (
    'ALLOWED_HOSTS',
    'BROADCAST_WEBSOCKET_PORT',
    'BROADCAST_WEBSOCKET_VERIFY_CERT',
    'BROADCAST_WEBSOCKET_PROTOCOL',
    'BROADCAST_WEBSOCKET_SECRET',
    'DATABASES',
    'CACHES',
    'DEBUG',
    'NAMED_URL_GRAPH',
    'DISPATCHER_MOCK_PUBLISH',
)


def test_postprocess_auth_basic_enabled():
    """The final loaded settings should have basic auth enabled."""
    from awx.settings import REST_FRAMEWORK

    assert 'awx.api.authentication.LoggedBasicAuthentication' in REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']


def test_default_settings():
    """Ensure that all default settings are present in the snapshot."""
    from django.conf import settings

    for k in dir(settings):
        if k not in settings.DEFAULTS_SNAPSHOT or k in LOCAL_SETTINGS:
            continue
        default_val = getattr(settings.default_settings, k, None)
        snapshot_val = settings.DEFAULTS_SNAPSHOT[k]
        assert default_val == snapshot_val, f'Setting for {k} does not match shapshot:\nsnapshot: {snapshot_val}\ndefault: {default_val}'


def test_django_conf_settings_is_awx_settings():
    """Ensure that the settings loaded from dynaconf are the same as the settings delivered to django."""
    from django.conf import settings
    from awx.settings import REST_FRAMEWORK

    assert settings.REST_FRAMEWORK == REST_FRAMEWORK


def test_dynaconf_is_awx_settings():
    """Ensure that the settings loaded from dynaconf are the same as the settings delivered to django."""
    from django.conf import settings
    from awx.settings import REST_FRAMEWORK

    assert settings.DYNACONF.REST_FRAMEWORK == REST_FRAMEWORK


def test_development_settings_can_be_directly_imported(monkeypatch):
    """Ensure that the development settings can be directly imported."""
    monkeypatch.setenv('AWX_MODE', 'development')
    from django.conf import settings
    from awx.settings.development import REST_FRAMEWORK
    from awx.settings.development import DEBUG  # actually set on defaults.py and not overridden in development.py

    assert settings.REST_FRAMEWORK == REST_FRAMEWORK
    assert DEBUG is True


def test_merge_application_name():
    """Ensure that the merge_application_name function works as expected."""
    from awx.settings.functions import merge_application_name

    settings = {
        "DATABASES__default__ENGINE": "django.db.backends.postgresql",
        "CLUSTER_HOST_ID": "test-cluster-host-id",
    }
    result = merge_application_name(settings)["DATABASES__default__OPTIONS__application_name"]
    assert result.startswith("awx-")
    assert "test-cluster" in result

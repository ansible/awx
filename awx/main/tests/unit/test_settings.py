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
    # Platform flags are managed by the platform flags system and have environment-specific defaults
    'FEATURE_DISPATCHERD_ENABLED',
    'FEATURE_INDIRECT_NODE_COUNTING_ENABLED',
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
        assert default_val == snapshot_val, f'Setting for {k} does not match snapshot:\nsnapshot: {snapshot_val}\ndefault: {default_val}'


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


def test_development_defaults_feature_flags(monkeypatch):
    """Ensure that development_defaults.py sets the correct feature flags."""
    monkeypatch.setenv('AWX_MODE', 'development')

    # Import the development_defaults module directly to trigger coverage of the new lines
    import importlib.util
    import os

    spec = importlib.util.spec_from_file_location("development_defaults", os.path.join(os.path.dirname(__file__), "../../../settings/development_defaults.py"))
    development_defaults = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(development_defaults)

    # Also import through the development settings to ensure both paths are tested
    from awx.settings.development import FEATURE_INDIRECT_NODE_COUNTING_ENABLED, FEATURE_DISPATCHERD_ENABLED

    # Verify the feature flags are set correctly in both the module and settings
    assert hasattr(development_defaults, 'FEATURE_INDIRECT_NODE_COUNTING_ENABLED')
    assert development_defaults.FEATURE_INDIRECT_NODE_COUNTING_ENABLED is True
    assert hasattr(development_defaults, 'FEATURE_DISPATCHERD_ENABLED')
    assert development_defaults.FEATURE_DISPATCHERD_ENABLED is True
    assert FEATURE_INDIRECT_NODE_COUNTING_ENABLED is True
    assert FEATURE_DISPATCHERD_ENABLED is True

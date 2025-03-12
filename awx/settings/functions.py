import os
from ansible_base.lib.dynamic_config import load_python_file_with_injected_context
from dynaconf import Dynaconf
from .application_name import get_application_name


def merge_application_name(settings):
    """Return a dynaconf merge dict to set the application name for the connection."""
    data = {}
    if "sqlite3" not in settings.get("DATABASES__default__ENGINE", ""):
        data["DATABASES__default__OPTIONS__application_name"] = get_application_name(settings.get("CLUSTER_HOST_ID"))
    return data


def add_backwards_compatibility():
    """Add backwards compatibility for AWX_MODE.

    Before dynaconf integration the usage of AWX settings was supported to be just
    DJANGO_SETTINGS_MODULE=awx.settings.production or DJANGO_SETTINGS_MODULE=awx.settings.development
    (development_quiet and development_kube were also supported).

    With dynaconf the DJANGO_SETTINGS_MODULE should be set always to "awx.settings" as the only entry point
    for settings  and then "AWX_MODE" can be set to any of production,development,quiet,kube
    or a combination of them separated by comma.

    E.g:

        export DJANGO_SETTINGS_MODULE=awx.settings
        export AWX_MODE=production
        awx-manage [command]
        dynaconf [command]

    If pointing `DJANGO_SETTINGS_MODULE` to `awx.settings.production` or `awx.settings.development` then
    this function will set `AWX_MODE` to the correct value.
    """
    django_settings_module = os.getenv("DJANGO_SETTINGS_MODULE", "awx.settings")
    if django_settings_module == "awx.settings":
        return

    current_mode = os.getenv("AWX_MODE", "")
    for _module_name in ["development", "production", "development_quiet", "development_kube"]:
        if django_settings_module == f"awx.settings.{_module_name}":
            _mode = current_mode.split(",")
            if "development_" in _module_name and "development" not in current_mode:
                _mode.append("development")
            _mode_fragment = _module_name.replace("development_", "")
            if _mode_fragment not in _mode:
                _mode.append(_mode_fragment)
            os.environ["AWX_MODE"] = ",".join(_mode)


def load_extra_development_files(settings: Dynaconf):
    """Load optional development only settings files."""
    if not settings.is_development_mode:
        return

    if settings.get_environ("AWX_KUBE_DEVEL"):
        load_python_file_with_injected_context("kube_defaults.py", settings=settings)
    else:
        load_python_file_with_injected_context("local_*.py", settings=settings)


def assert_production_settings(settings: Dynaconf, settings_dir: str, settings_file_path: str):  # pragma: no cover
    """Ensure at least one setting file has been loaded in production mode.
    Current systems will require /etc/tower/settings.py and
    new systems will require /etc/ansible-automation-platform/*.yaml
    """
    if "production" not in settings.current_env.lower():
        return

    required_settings_paths = [
        os.path.dirname(settings_file_path),
        "/etc/ansible-automation-platform/",
        settings_dir,
    ]

    for path in required_settings_paths:
        if any([path in os.path.dirname(f) for f in settings._loaded_files]):
            break
    else:
        from django.core.exceptions import ImproperlyConfigured  # noqa

        msg = 'No AWX configuration found at %s.' % required_settings_paths
        msg += '\nDefine the AWX_SETTINGS_FILE environment variable to '
        msg += 'specify an alternate path.'
        raise ImproperlyConfigured(msg)

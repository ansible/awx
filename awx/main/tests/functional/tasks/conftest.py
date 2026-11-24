import pytest

from awx.conf import settings_registry

_FLAGS = ('read_only', 'defined_in_file')


@pytest.fixture(autouse=True)
def restore_conf_registry_flags():
    """Put the awx.conf registry flags back after each test.

    awx.conf marks a setting read-only when its one-time check runs under pytest-django's settings
    override. The registry is shared by the whole process and the mark is never reset, so a later
    test on the same worker could no longer set those settings.
    """
    saved = {key: {flag: field[flag] for flag in _FLAGS if flag in field} for key, field in settings_registry._registry.items()}
    yield
    for key, field in settings_registry._registry.items():
        for flag in _FLAGS:
            if flag in saved.get(key, {}):
                field[flag] = saved[key][flag]
            else:
                field.pop(flag, None)

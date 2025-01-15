from django.conf import settings

from awx.main.utils.db import get_listener_params


def test_get_listener_params():
    params = get_listener_params()
    assert params['autocommit'] == True
    assert params['dbname'] == settings.DATABASES['default']['NAME']  # artifical, is sqlite3
    assert 'application_name' in params

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import pytest

from awx.conf.models import Setting


@pytest.mark.django_db
def test_setting_bool_value(run_module, admin_user):
    for the_value in (True, False):
        result = run_module('settings', dict(name='ACTIVITY_STREAM_ENABLED_FOR_INVENTORY_SYNC', value=the_value), admin_user)
        assert not result.get('failed', False), result.get('msg', result)
        assert result.get('changed'), result

        assert Setting.objects.get(key='ACTIVITY_STREAM_ENABLED_FOR_INVENTORY_SYNC').value is the_value

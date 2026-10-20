import pytest
from django.conf import settings
from django.core.management import call_command

from awx.conf.models import Setting


@pytest.mark.django_db
@pytest.mark.parametrize(
    ('option', 'expected'),
    [
        ('--enable', True),
        ('--disable', False),
    ],
)
def test_set_indirect_node_counting_persists_setting(option, expected, mocker):
    mocker.patch('awx.main.management.commands.set_indirect_node_counting.clear_setting_cache')

    call_command('set_indirect_node_counting', option)

    assert Setting.objects.get(key='INDIRECT_NODE_COUNTING_ENABLED', user=None).value is expected
    settings._awx_conf_memoizedcache.clear()
    assert settings.INDIRECT_NODE_COUNTING_ENABLED is expected

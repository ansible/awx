import pytest
from django.core.management import call_command
from django.core.management.base import CommandError


@pytest.mark.parametrize(
    ('option', 'expected'),
    [
        ('--enable', True),
        ('--disable', False),
    ],
)
def test_set_indirect_node_counting(option, expected, mocker):
    mock_settings = mocker.patch('awx.main.management.commands.set_indirect_node_counting.settings')
    mock_clear_cache = mocker.patch('awx.main.management.commands.set_indirect_node_counting.clear_setting_cache')

    call_command('set_indirect_node_counting', option)

    assert mock_settings.INDIRECT_NODE_COUNTING_ENABLED is expected
    mock_clear_cache.delay.assert_called_once_with(['INDIRECT_NODE_COUNTING_ENABLED'])


def test_set_indirect_node_counting_requires_an_option():
    with pytest.raises(CommandError, match='one of the arguments'):
        call_command('set_indirect_node_counting')

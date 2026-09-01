import pytest
from django.core.management.base import CommandError

from awx.main.management.commands.set_indirect_node_counting import Command


@pytest.mark.parametrize(
    ('options', 'expected'),
    [
        ({'enable': True, 'disable': False}, True),
        ({'enable': False, 'disable': True}, False),
    ],
)
def test_set_indirect_node_counting(options, expected, mocker):
    mock_settings = mocker.patch('awx.main.management.commands.set_indirect_node_counting.settings')
    mock_clear_cache = mocker.patch('awx.main.management.commands.set_indirect_node_counting.clear_setting_cache')

    Command().handle(**options)

    assert mock_settings.INDIRECT_NODE_COUNTING_ENABLED is expected
    mock_clear_cache.delay.assert_called_once_with(['INDIRECT_NODE_COUNTING_ENABLED'])


def test_set_indirect_node_counting_requires_an_option():
    with pytest.raises(CommandError, match='Pass either'):
        Command().handle(enable=False, disable=False)

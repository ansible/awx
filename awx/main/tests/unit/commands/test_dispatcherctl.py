import io

import pytest

from django.core.management.base import CommandError

from awx.main.management.commands import dispatcherctl


@pytest.fixture(autouse=True)
def clear_dispatcher_env(monkeypatch, mocker):
    monkeypatch.delenv('DISPATCHERD_CONFIG_FILE', raising=False)
    mocker.patch.object(dispatcherctl.logging, 'basicConfig')
    mocker.patch.object(dispatcherctl, 'connection', mocker.Mock(vendor='postgresql'))


def test_dispatcherctl_runs_control_with_generated_config(mocker):
    command = dispatcherctl.Command()
    command.stdout = io.StringIO()

    data = {'foo': 'bar'}
    mocker.patch.object(dispatcherctl, '_build_command_data_from_args', return_value=data)
    dispatcher_setup = mocker.patch.object(dispatcherctl, 'dispatcher_setup')
    config_data = {'setting': 'value'}
    mocker.patch.object(dispatcherctl, 'get_dispatcherd_config', return_value=config_data)

    control = mocker.Mock()
    control.control_with_reply.return_value = [{'status': 'ok'}]
    mocker.patch.object(dispatcherctl, 'get_control_from_settings', return_value=control)
    mocker.patch.object(dispatcherctl.yaml, 'dump', return_value='payload\n')

    command.handle(
        command='running',
        config=dispatcherctl.DEFAULT_CONFIG_FILE,
        expected_replies=1,
        log_level='INFO',
    )

    dispatcher_setup.assert_called_once_with(config_data)
    control.control_with_reply.assert_called_once_with('running', data=data, expected_replies=1)
    assert command.stdout.getvalue() == 'payload\n'


def test_dispatcherctl_rejects_custom_config_path():
    command = dispatcherctl.Command()
    command.stdout = io.StringIO()

    with pytest.raises(CommandError):
        command.handle(
            command='running',
            config='/tmp/dispatcher.yml',
            expected_replies=1,
            log_level='INFO',
        )


def test_dispatcherctl_rejects_sqlite_db(mocker):
    command = dispatcherctl.Command()
    command.stdout = io.StringIO()

    mocker.patch.object(dispatcherctl, 'connection', mocker.Mock(vendor='sqlite'))

    with pytest.raises(CommandError, match='sqlite3'):
        command.handle(
            command='running',
            config=dispatcherctl.DEFAULT_CONFIG_FILE,
            expected_replies=1,
            log_level='INFO',
        )


def test_dispatcherctl_raises_when_replies_missing(mocker):
    command = dispatcherctl.Command()
    command.stdout = io.StringIO()

    mocker.patch.object(dispatcherctl, '_build_command_data_from_args', return_value={})
    mocker.patch.object(dispatcherctl, 'dispatcher_setup')
    mocker.patch.object(dispatcherctl, 'get_dispatcherd_config', return_value={})
    control = mocker.Mock()
    control.control_with_reply.return_value = [{'status': 'ok'}]
    mocker.patch.object(dispatcherctl, 'get_control_from_settings', return_value=control)
    mocker.patch.object(dispatcherctl.yaml, 'dump', return_value='- status: ok\n')

    with pytest.raises(CommandError):
        command.handle(
            command='running',
            config=dispatcherctl.DEFAULT_CONFIG_FILE,
            expected_replies=2,
            log_level='INFO',
        )

    control.control_with_reply.assert_called_once_with('running', data={}, expected_replies=2)

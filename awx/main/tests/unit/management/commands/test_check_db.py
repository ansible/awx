import pytest
from django.core.management.base import CommandError

from awx.main.management.commands.check_db import Command


def test_check_db_command_success(mocker):
    mock_cursor = mocker.MagicMock()
    mock_cursor.fetchone.return_value = ['PostgreSQL 12.8 on x86_64-pc-linux-gnu, compiled by gcc (GCC) 9.3.0, 64-bit']
    mock_connection = mocker.MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mocker.patch('awx.main.management.commands.check_db.connection', mock_connection)
    mocker.patch('awx.main.management.commands.check_db.db_requirement_violations', return_value=None)

    command = Command()
    result = command.handle()

    assert 'Database Version:' in result
    mock_cursor.execute.assert_called_once_with('SELECT version()')


def test_check_db_command_version_violations(mocker):
    mock_cursor = mocker.MagicMock()
    mock_cursor.fetchone.return_value = ['PostgreSQL 11.0 on x86_64-pc-linux-gnu']
    mock_connection = mocker.MagicMock()
    mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
    mocker.patch('awx.main.management.commands.check_db.connection', mock_connection)
    violation_msg = "At a minimum, postgres version 12 is required, found 11\n"
    mocker.patch('awx.main.management.commands.check_db.db_requirement_violations', return_value=violation_msg)

    command = Command()
    with pytest.raises(CommandError) as exc_info:
        command.handle()

    assert str(exc_info.value) == violation_msg

import re
import pytest
xfail = pytest.mark.xfail


def test_open_shell_and_close_shell(protocol_real):
    shell_id = protocol_real.open_shell()
    assert re.match('^\w{8}-\w{4}-\w{4}-\w{4}-\w{12}$', shell_id)

    protocol_real.close_shell(shell_id)


def test_run_command_with_arguments_and_cleanup_command(protocol_real):
    shell_id = protocol_real.open_shell()
    command_id = protocol_real.run_command(shell_id, 'ipconfig', ['/all'])
    assert re.match('^\w{8}-\w{4}-\w{4}-\w{4}-\w{12}$', command_id)

    protocol_real.cleanup_command(shell_id, command_id)
    protocol_real.close_shell(shell_id)


def test_run_command_without_arguments_and_cleanup_command(protocol_real):
    shell_id = protocol_real.open_shell()
    command_id = protocol_real.run_command(shell_id, 'hostname')
    assert re.match('^\w{8}-\w{4}-\w{4}-\w{4}-\w{12}$', command_id)

    protocol_real.cleanup_command(shell_id, command_id)
    protocol_real.close_shell(shell_id)


def test_get_command_output(protocol_real):
    shell_id = protocol_real.open_shell()
    command_id = protocol_real.run_command(shell_id, 'ipconfig', ['/all'])
    std_out, std_err, status_code = protocol_real.get_command_output(
        shell_id, command_id)

    assert status_code == 0
    assert 'Windows IP Configuration' in std_out
    assert len(std_err) == 0

    protocol_real.cleanup_command(shell_id, command_id)
    protocol_real.close_shell(shell_id)


def test_run_command_taking_more_than_60_seconds(protocol_real):
    shell_id = protocol_real.open_shell()
    command_id = protocol_real.run_command(shell_id, 'PowerShell -Command Start-Sleep -s 75')
    assert re.match('^\w{8}-\w{4}-\w{4}-\w{4}-\w{12}$', command_id)
    std_out, std_err, status_code = protocol_real.get_command_output(
        shell_id, command_id)

    assert status_code == 0
    assert len(std_err) == 0

    protocol_real.cleanup_command(shell_id, command_id)
    protocol_real.close_shell(shell_id)


@xfail()
def test_set_timeout(protocol_real):
    raise NotImplementedError()


@xfail()
def test_set_max_env_size(protocol_real):
    raise NotImplementedError()


@xfail()
def test_set_locale(protocol_real):
    raise NotImplementedError()
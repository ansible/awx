def test_open_shell_and_close_shell(protocol_fake):
    shell_id = protocol_fake.open_shell()
    assert shell_id == '11111111-1111-1111-1111-111111111113'

    protocol_fake.close_shell(shell_id)


def test_run_command_with_arguments_and_cleanup_command(protocol_fake):
    shell_id = protocol_fake.open_shell()
    command_id = protocol_fake.run_command(shell_id, 'ipconfig', ['/all'])
    assert command_id == '11111111-1111-1111-1111-111111111114'

    protocol_fake.cleanup_command(shell_id, command_id)
    protocol_fake.close_shell(shell_id)


def test_run_command_without_arguments_and_cleanup_command(protocol_fake):
    shell_id = protocol_fake.open_shell()
    command_id = protocol_fake.run_command(shell_id, 'hostname')
    assert command_id == '11111111-1111-1111-1111-111111111114'

    protocol_fake.cleanup_command(shell_id, command_id)
    protocol_fake.close_shell(shell_id)


def test_get_command_output(protocol_fake):
    shell_id = protocol_fake.open_shell()
    command_id = protocol_fake.run_command(shell_id, 'ipconfig', ['/all'])
    std_out, std_err, status_code = protocol_fake.get_command_output(shell_id, command_id)
    assert status_code == 0
    assert 'Windows IP Configuration' in std_out
    assert len(std_err) == 0

    protocol_fake.cleanup_command(shell_id, command_id)
    protocol_fake.close_shell(shell_id)
import sys
import pytest

from io import StringIO

from django.core.management import call_command

from awx.main.management.commands.update_password import UpdatePassword


def run_command(name, *args, **options):
    command_runner = options.pop('command_runner', call_command)
    stdin_fileobj = options.pop('stdin_fileobj', None)
    options.setdefault('verbosity', 1)
    original_stdin = sys.stdin
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    if stdin_fileobj:
        sys.stdin = stdin_fileobj
    sys.stdout = StringIO()
    sys.stderr = StringIO()
    result = None
    try:
        result = command_runner(name, *args, **options)
    except Exception as e:
        result = e
    finally:
        captured_stdout = sys.stdout.getvalue()
        captured_stderr = sys.stderr.getvalue()
        sys.stdin = original_stdin
        sys.stdout = original_stdout
        sys.stderr = original_stderr
    return result, captured_stdout, captured_stderr


@pytest.mark.parametrize(
    "username,password,expected,changed", [
        ('admin', 'dingleberry', 'Password updated', True),
        ('admin', 'admin', 'Password not updated', False),
        (None, 'foo', 'username required', False),
        ('admin', None, 'password required', False),
    ]
)
def test_update_password_command(mocker, username, password, expected, changed):
    with mocker.patch.object(UpdatePassword, 'update_password', return_value=changed):
        result, stdout, stderr = run_command('update_password', username=username, password=password)
        if result is None:
            assert stdout == expected
        else:
            assert str(result) == expected

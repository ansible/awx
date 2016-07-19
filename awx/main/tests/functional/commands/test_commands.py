import sys
import pytest

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from django.core.management import call_command

from awx.main.models import Instance

from awx.main.management.commands.update_password import UpdatePassword
from awx.main.management.commands.remove_instance import Command as RemoveInstance

def run_command(name, *args, **options):
    command_runner = options.pop('command_runner', call_command)
    stdin_fileobj = options.pop('stdin_fileobj', None)
    options.setdefault('verbosity', 1)
    options.setdefault('interactive', False)
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
        ('admin', 'dingleberry', 'Password updated\n', True),
        ('admin', 'admin', 'Password not updated\n', False),
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


@pytest.mark.parametrize(
    "primary,hostname,startswith,exception", [
        (True, "127.0.0.1", "Cannot remove primary", None),
        (False, "127.0.0.2", "Successfully removed", None),
        (False, "127.0.0.3", "No matching instance", Instance.DoesNotExist),
    ]
)
def test_remove_instance_command(mocker, primary, hostname, startswith, exception):
    mock_instance = mocker.MagicMock(primary=primary, enforce_unique_find=True)
    with mocker.patch.object(Instance.objects, 'get', return_value=mock_instance, side_effect=exception):
        with mocker.patch.object(RemoveInstance, 'include_option_hostname_uuid_find'):
            with mocker.patch.object(RemoveInstance, 'get_unique_fields', return_value={'hostname':hostname, 'uuid':1}):
                    result, stdout, stderr = run_command("remove_instance", hostname=hostname)
                    if result is None:
                        assert stdout.startswith(startswith)
                    else:
                        assert str(result).startswith(startswith)

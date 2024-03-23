import sys
import pytest

from io import StringIO

from django.core.management import call_command

from awx.main.management.commands.update_password import UpdatePassword
from awx.main.models import Schedule
from awx.main.tests.factories.fixtures import mk_job_template, mk_schedule, mk_system_job_template


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
    "username,password,expected,changed",
    [
        ('admin', 'dingleberry', 'Password updated', True),
        ('admin', 'admin', 'Password not updated', False),
        (None, 'foo', 'username required', False),
        ('admin', None, 'password required', False),
    ],
)
def test_update_password_command(mocker, username, password, expected, changed):
    with mocker.patch.object(UpdatePassword, 'update_password', return_value=changed):
        result, stdout, stderr = run_command('update_password', username=username, password=password)
        if result is None:
            assert stdout == expected
        else:
            assert str(result) == expected


@pytest.mark.django_db
class TestCleanupSchedulesCases:
    def mk_rrule_str(self, only_once=False):
        rrule_str = "DTSTART:20200101T000000Z RRULE:FREQ=DAILY"
        if only_once:
            rrule_str += ";COUNT=1"
        return rrule_str

    @pytest.mark.parametrize(
        "enabled,only_once",
        [
            (True, True),
            (True, False),
            (False, False),
        ],
    )
    def test_never_cleanup_system_job_shedules(self, enabled, only_once):
        sjt = mk_system_job_template(name="Cleanup Schedules")
        mk_schedule(name="Cleanup Schedules", unified_job_template=sjt, rrule=self.mk_rrule_str(only_once=only_once), enabled=enabled)

        run_command("cleanup_schedules", days=0)

        assert Schedule.objects.count() == 1

    @pytest.mark.parametrize(
        "skip_disabled,enabled,only_once,expected",
        [
            (True, True, True, 0),
            (True, True, False, 1),
            (True, False, False, 1),
            (False, True, True, 0),
            (False, True, False, 1),
            (False, False, False, 0),
        ],
    )
    def test_cleanup_schedules_of_regular_job_schedule(self, skip_disabled, enabled, only_once, expected):
        jt = mk_job_template(name="Test")
        mk_schedule(name="Test", unified_job_template=jt, rrule=self.mk_rrule_str(only_once=only_once), enabled=enabled)
        run_command("cleanup_schedules", skip_disabled=skip_disabled)

        assert Schedule.objects.count() == expected

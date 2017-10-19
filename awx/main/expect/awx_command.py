import logging
import time
import sys

# AWX
from awx.main.utils.common import set_environ
from awx.main.exceptions import TaskCancel, TaskTimedout

# Django
from django.core.management import get_commands, load_command_class, call_command


logger = logging.getLogger('awx.main.utils.expect.awx_command')


class CallbackHandler(logging.Handler):
    '''
    Not an actual log handler, only acts as a callback for system actions
    such as cancel and timing out.
    Class sets level to 'DEBUG' and thus will be called more frequently
    than the handler that writes to the logfile, allowing for faster canceling.
    '''

    def __init__(self, cancelled_callback, job_timeout, level=0):
        self.cancelled_callback = cancelled_callback
        self.job_timeout = job_timeout
        self.job_start = time.time()
        super(CallbackHandler, self).__init__(level=logging.DEBUG)

    def emit(self, record):
        try:
            canceled = self.cancelled_callback()
        except:
            raise Exception('Could not check cancel callback - canceling immediately')

        if canceled:
            raise TaskCancel(None, 1)

        if self.job_timeout != 0 and (time.time() - self.job_start) > self.job_timeout:
            raise TaskTimedout(None, 1)

        pass  # Nope, not actually emiting a log message


class StdoutRedirect:
    def __init__(self, new_handle):
        self.new_handle = new_handle

    def __enter__(self):
        self.old_handle = sys.stdout
        sys.stdout = self.new_handle

    def __exit__(self, type, value, traceback):
        sys.stdout = self.old_handle


def run_command(args, cwd, env, logfile,
                cancelled_callback=None,
                extra_update_fields=None, job_timeout=0,
                pexpect_timeout=5, proot_cmd='bwrap'):
    '''
    Run the given management command, invoking directly, but using the
    logger to check the callback module.

    :param args:                a list of `subprocess.call`-style arguments
                                representing a subprocess e.g., ['ls', '-la']
    :param cwd:                 the directory in which the subprocess should
                                run
    :param env:                 a dict containing environment variables for the
                                subprocess, ala `os.environ`
    :param logfile:             a file-like object for capturing stdout
    :param cancelled_callback:  a callable - which returns `True` or `False`
                                - signifying if the job has been prematurely
                                  cancelled
    :param extra_update_fields: a dict used to specify DB fields which should
                                be updated on the underlying model
                                object after execution completes
    :param job_timeout          a timeout (in seconds); if the total job runtime
                                exceeds this, the process will be killed
    :param pexpect_timeout      a timeout (in seconds) to wait on
                                `pexpect.spawn().expect()` calls
    :param proot_cmd            the command used to isolate processes, `bwrap`

    Returns a tuple (status, return_code) i.e., `('successful', 0)`
    '''
    command_name = args[1]

    # Equip logger for cancelled_callback
    callback_handler = CallbackHandler(cancelled_callback, job_timeout)
    cmd_logger = logging.getLogger('awx.main.management.commands.{}'.format(command_name))
    cmd_logger.addHandler(callback_handler)

    # turn args into kwargs
    command = load_command_class(get_commands()[command_name], command_name)
    parser = command.create_parser('awx-manage', command_name)
    options, _ = parser.parse_args(args[2:])
    options = vars(options)

    try:
        with set_environ(**env), StdoutRedirect(logfile):
            call_command(command_name, **options)
    except TaskCancel:
        return 'canceled', 1
    except TaskTimedout:
        extra_update_fields['job_explanation'] = "Job terminated due to timeout"
        return 'error', 1
    except Exception:
        if isinstance(extra_update_fields, dict):
            extra_update_fields['job_explanation'] = (
                "System error during job execution, check system logs")
        return 'error', 1
    finally:
        # Remove the callback handler
        cmd_logger.handlers = [
            h for h in cmd_logger.handlers if not isinstance(h, CallbackHandler)
        ]

    return 'successful', 0

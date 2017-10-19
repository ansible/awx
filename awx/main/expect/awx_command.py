import logging
import time

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

    def __init__(self, task, cancelled_callback, job_timeout, level=0):
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

    callback_handler = CallbackHandler(task, cancelled_callback, job_timeout)

    # Equip logger for stdout_handle and cancelled_callback
    cmd_logger = logging.getLogger('awx.main.management.commands.{}'.format(command_name))
    cmd_logger.addHandler(callback_handler)
    old_stdout = cmd_logger.handlers[0].stream
    import_logger.handlers[0].stream = stdout_handle

    # turn args into kwargs
    command = load_command_class(get_commands()[command_name], command_name)
    parser = command.create_parser('awx-manage', command_name)
    options, _ = parser.parse_args(args[2:])
    options = vars(options)

    try:
        with set_environ(**env):
            call_command(command_name, **options)
    except TaskCancel as exc:
        pass
    except TaskTimedout as exc:
        extra_update_fields['job_explanation'] = "Job terminated due to timeout"
        return 'error', 1
    except Exception as exc:
        if isinstance(extra_update_fields, dict):
            extra_update_fields['job_explanation'] = (
                "System error during job execution, check system logs"
            )
        return 'error', 1
    finally:
        cmd_logger.handlers[0].stream = old_stdout

    return 'successful', child.exitstatus

#! /usr/bin/env python

import argparse
import base64
import codecs
import collections
import logging
import json
import os
import stat
import pipes
import re
import signal
import sys
import threading
import time
try:
    from io import StringIO
except ImportError:
    from StringIO import StringIO

import pexpect
import psutil


logger = logging.getLogger('awx.main.utils.expect')


def args2cmdline(*args):
    return ' '.join([pipes.quote(a) for a in args])


def wrap_args_with_ssh_agent(args, ssh_key_path, ssh_auth_sock=None, silence_ssh_add=False):
    if ssh_key_path:
        ssh_add_command = args2cmdline('ssh-add', ssh_key_path)
        if silence_ssh_add:
            ssh_add_command = ' '.join([ssh_add_command, '2>/dev/null'])
        cmd = ' && '.join([ssh_add_command,
                           args2cmdline('rm', '-f', ssh_key_path),
                           args2cmdline(*args)])
        args = ['ssh-agent']
        if ssh_auth_sock:
            args.extend(['-a', ssh_auth_sock])
        args.extend(['sh', '-c', cmd])
    return args


def open_fifo_write(path, data):
    '''open_fifo_write opens the fifo named pipe in a new thread.
    This blocks the thread until an external process (such as ssh-agent)
    reads data from the pipe.
    '''
    os.mkfifo(path, 0o600)
    threading.Thread(
        target=lambda p, d: open(p, 'w').write(d),
        args=(path, data)
    ).start()


def run_pexpect(args, cwd, env, logfile,
                cancelled_callback=None, expect_passwords={},
                extra_update_fields=None, idle_timeout=None, job_timeout=0,
                pexpect_timeout=5, proot_cmd='bwrap'):
    '''
    Run the given command using pexpect to capture output and provide
    passwords when requested.

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
    :param expect_passwords:    a dict of regular expression password prompts
                                to input values, i.e., {r'Password:*?$':
                                'some_password'}
    :param extra_update_fields: a dict used to specify DB fields which should
                                be updated on the underlying model
                                object after execution completes
    :param idle_timeout         a timeout (in seconds); if new output is not
                                sent to stdout in this interval, the process
                                will be terminated
    :param job_timeout          a timeout (in seconds); if the total job runtime
                                exceeds this, the process will be killed
    :param pexpect_timeout      a timeout (in seconds) to wait on
                                `pexpect.spawn().expect()` calls
    :param proot_cmd            the command used to isolate processes, `bwrap`

    Returns a tuple (status, return_code) i.e., `('successful', 0)`
    '''
    expect_passwords[pexpect.TIMEOUT] = None
    expect_passwords[pexpect.EOF] = None

    if not isinstance(expect_passwords, collections.OrderedDict):
        # We iterate over `expect_passwords.keys()` and
        # `expect_passwords.values()` separately to map matched inputs to
        # patterns and choose the proper string to send to the subprocess;
        # enforce usage of an OrderedDict so that the ordering of elements in
        # `keys()` matches `values()`.
        expect_passwords = collections.OrderedDict(expect_passwords)
    password_patterns = list(expect_passwords.keys())
    password_values = list(expect_passwords.values())

    child = pexpect.spawn(
        args[0], args[1:], cwd=cwd, env=env, ignore_sighup=True,
        encoding='utf-8', echo=False, use_poll=True
    )
    child.logfile_read = logfile
    canceled = False
    timed_out = False
    errored = False
    last_stdout_update = time.time()

    job_start = time.time()
    while child.isalive():
        result_id = child.expect(password_patterns, timeout=pexpect_timeout, searchwindowsize=100)
        password = password_values[result_id]
        if password is not None:
            child.sendline(password)
            last_stdout_update = time.time()
        if cancelled_callback:
            try:
                canceled = cancelled_callback()
            except Exception:
                logger.exception('Could not check cancel callback - canceling immediately')
                if isinstance(extra_update_fields, dict):
                    extra_update_fields['job_explanation'] = "System error during job execution, check system logs"
                errored = True
        else:
            canceled = False
        if not canceled and job_timeout != 0 and (time.time() - job_start) > job_timeout:
            timed_out = True
            if isinstance(extra_update_fields, dict):
                extra_update_fields['job_explanation'] = "Job terminated due to timeout"
        if canceled or timed_out or errored:
            handle_termination(child.pid, child.args, proot_cmd, is_cancel=canceled)
        if idle_timeout and (time.time() - last_stdout_update) > idle_timeout:
            child.close(True)
            canceled = True
    if errored:
        return 'error', child.exitstatus
    elif canceled:
        return 'canceled', child.exitstatus
    elif child.exitstatus == 0 and not timed_out:
        return 'successful', child.exitstatus
    else:
        return 'failed', child.exitstatus


def run_isolated_job(private_data_dir, secrets, logfile=sys.stdout):
    '''
    Launch `ansible-playbook`, executing a job packaged by
    `build_isolated_job_data`.

    :param private_data_dir:  an absolute path on the local file system where
                              job metadata exists (i.e.,
                              `/tmp/ansible_awx_xyz/`)
    :param secrets:           a dict containing sensitive job metadata, {
                                  'env': { ... }  # environment variables,
                                  'passwords': { ... } # pexpect password prompts
                                  'ssh_key_data': 'RSA KEY DATA',
                              }
    :param logfile:           a file-like object for capturing stdout

    Returns a tuple (status, return_code) i.e., `('successful', 0)`
    '''
    with open(os.path.join(private_data_dir, 'args'), 'r') as args:
        args = json.load(args)

    env = secrets.get('env', {})
    expect_passwords = {
        re.compile(pattern, re.M): password
        for pattern, password in secrets.get('passwords', {}).items()
    }

    if 'AD_HOC_COMMAND_ID' in env:
        cwd = private_data_dir
    else:
        cwd = os.path.join(private_data_dir, 'project')

    # write the SSH key data into a fifo read by ssh-agent
    ssh_key_data = secrets.get('ssh_key_data')
    if ssh_key_data:
        ssh_key_path = os.path.join(private_data_dir, 'ssh_key_data')
        ssh_auth_sock = os.path.join(private_data_dir, 'ssh_auth.sock')
        open_fifo_write(ssh_key_path, ssh_key_data)
        args = wrap_args_with_ssh_agent(args, ssh_key_path, ssh_auth_sock)

    idle_timeout = secrets.get('idle_timeout', 10)
    job_timeout = secrets.get('job_timeout', 10)
    pexpect_timeout = secrets.get('pexpect_timeout', 5)

    # Use local callback directory
    callback_dir = os.getenv('AWX_LIB_DIRECTORY')
    if callback_dir is None:
        raise RuntimeError('Location for callbacks must be specified '
                           'by environment variable AWX_LIB_DIRECTORY.')
    env['ANSIBLE_CALLBACK_PLUGINS'] = os.path.join(callback_dir, 'isolated_callbacks')
    if 'AD_HOC_COMMAND_ID' in env:
        env['ANSIBLE_STDOUT_CALLBACK'] = 'minimal'
    else:
        env['ANSIBLE_STDOUT_CALLBACK'] = 'awx_display'
    env['AWX_ISOLATED_DATA_DIR'] = private_data_dir
    env['PYTHONPATH'] = env.get('PYTHONPATH', '') + callback_dir + ':'

    venv_path = env.get('VIRTUAL_ENV')
    if venv_path and not os.path.exists(venv_path):
        raise RuntimeError(
            'a valid Python virtualenv does not exist at {}'.format(venv_path)
        )

    return run_pexpect(args, cwd, env, logfile,
                       expect_passwords=expect_passwords,
                       idle_timeout=idle_timeout,
                       job_timeout=job_timeout,
                       pexpect_timeout=pexpect_timeout)


def handle_termination(pid, args, proot_cmd, is_cancel=True):
    '''
    Terminate a subprocess spawned by `pexpect`.

    :param pid:       the process id of the running the job.
    :param args:      the args for the job, i.e., ['ansible-playbook', 'abc.yml']
    :param proot_cmd  the command used to isolate processes i.e., `bwrap`
    :param is_cancel: flag showing whether this termination is caused by
                      instance's cancel_flag.
    '''
    try:
        if sys.version_info > (3, 0):
            used_proot = proot_cmd.encode('utf-8') in args
        else:
            used_proot = proot_cmd in ' '.join(args)
        if used_proot:
            if not psutil:
                os.kill(pid, signal.SIGKILL)
            else:
                try:
                    main_proc = psutil.Process(pid=pid)
                    child_procs = main_proc.children(recursive=True)
                    for child_proc in child_procs:
                        os.kill(child_proc.pid, signal.SIGKILL)
                    os.kill(main_proc.pid, signal.SIGKILL)
                except (TypeError, psutil.Error):
                    os.kill(pid, signal.SIGKILL)
        else:
            os.kill(pid, signal.SIGTERM)
        time.sleep(3)
    except OSError:
        keyword = 'cancel' if is_cancel else 'timeout'
        logger.warn("Attempted to %s already finished job, ignoring" % keyword)


def __run__(private_data_dir):
    buff = StringIO()
    with codecs.open(os.path.join(private_data_dir, 'env'), 'r', encoding='utf-8') as f:
        for line in f:
            buff.write(line)

    artifacts_dir = os.path.join(private_data_dir, 'artifacts')

    # Standard out directed to pickup location without event filtering applied
    stdout_filename = os.path.join(artifacts_dir, 'stdout')
    os.mknod(stdout_filename, stat.S_IFREG | stat.S_IRUSR | stat.S_IWUSR)
    stdout_handle = codecs.open(stdout_filename, 'w', encoding='utf-8')

    status, rc = run_isolated_job(
        private_data_dir,
        json.loads(base64.b64decode(buff.getvalue())),
        stdout_handle
    )
    for filename, data in [
        ('status', status),
        ('rc', rc),
    ]:
        artifact_path = os.path.join(private_data_dir, 'artifacts', filename)
        os.mknod(artifact_path, stat.S_IFREG | stat.S_IRUSR | stat.S_IWUSR)
        with open(artifact_path, 'w') as f:
            f.write(str(data))


if __name__ == '__main__':
    import awx
    __version__ = awx.__version__
    parser = argparse.ArgumentParser(description='manage a daemonized, isolated ansible playbook')
    parser.add_argument('--version', action='version', version=__version__ + '-isolated')
    parser.add_argument('command', choices=['start', 'stop', 'is-alive'])
    parser.add_argument('private_data_dir')
    args = parser.parse_args()

    private_data_dir = args.private_data_dir
    pidfile = os.path.join(private_data_dir, 'pid')

    if args.command == 'start':
        # create a file to log stderr in case the daemonized process throws
        # an exception before it gets to `pexpect.spawn`
        stderr_path = os.path.join(private_data_dir, 'artifacts', 'daemon.log')
        if not os.path.exists(stderr_path):
            os.mknod(stderr_path, stat.S_IFREG | stat.S_IRUSR | stat.S_IWUSR)
        stderr = open(stderr_path, 'w+')

        import daemon
        from daemon.pidfile import TimeoutPIDLockFile
        context = daemon.DaemonContext(
            pidfile=TimeoutPIDLockFile(pidfile),
            stderr=stderr
        )
        with context:
            __run__(private_data_dir)
        sys.exit(0)

    try:
        with open(pidfile, 'r') as f:
            pid = int(f.readline())
    except IOError:
        sys.exit(1)

    if args.command == 'stop':
        try:
            with open(os.path.join(private_data_dir, 'args'), 'r') as args:
                handle_termination(pid, json.load(args), 'bwrap')
        except IOError:
            handle_termination(pid, [], 'bwrap')
    elif args.command == 'is-alive':
        try:
            os.kill(pid, signal.SIG_DFL)
            sys.exit(0)
        except OSError:
            sys.exit(1)

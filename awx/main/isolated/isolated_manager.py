import base64
import cStringIO
import codecs
import StringIO
import json
import os
import re
import stat
import time
import logging

from django.conf import settings

import awx
from awx.main.isolated import run
from awx.main.utils import OutputEventFilter
from awx.main.queue import CallbackQueueDispatcher

logger = logging.getLogger('awx.isolated.manager')


class IsolatedManager(object):

    def __init__(self, args, cwd, env, stdout_handle, ssh_key_path,
                 expect_passwords={},  cancelled_callback=None, job_timeout=0,
                 idle_timeout=None, extra_update_fields=None,
                 pexpect_timeout=5, proot_cmd='bwrap'):
        """
        :param args:                a list of `subprocess.call`-style arguments
                                    representing a subprocess e.g.,
                                    ['ansible-playbook', '...']
        :param cwd:                 the directory where the subprocess should run,
                                    generally the directory where playbooks exist
        :param env:                 a dict containing environment variables for the
                                    subprocess, ala `os.environ`
        :param stdout_handle:       a file-like object for capturing stdout
        :param ssh_key_path:        a filepath where SSH key data can be read
        :param expect_passwords:    a dict of regular expression password prompts
                                    to input values, i.e., {r'Password:\s*?$':
                                    'some_password'}
        :param cancelled_callback:  a callable - which returns `True` or `False`
                                    - signifying if the job has been prematurely
                                      cancelled
        :param job_timeout          a timeout (in seconds); if the total job runtime
                                    exceeds this, the process will be killed
        :param idle_timeout         a timeout (in seconds); if new output is not
                                    sent to stdout in this interval, the process
                                    will be terminated
        :param extra_update_fields: a dict used to specify DB fields which should
                                    be updated on the underlying model
                                    object after execution completes
        :param pexpect_timeout      a timeout (in seconds) to wait on
                                    `pexpect.spawn().expect()` calls
        :param proot_cmd            the command used to isolate processes, `bwrap`
        """
        self.args = args
        self.cwd = cwd
        self.env = env.copy()
        # Do not use callbacks for controller's management jobs
        self.env['ANSIBLE_CALLBACK_PLUGINS'] = ''
        self.env['CALLBACK_QUEUE'] = ''
        self.env['CALLBACK_CONNECTION'] = ''
        self.stdout_handle = stdout_handle
        self.ssh_key_path = ssh_key_path
        self.expect_passwords = {k.pattern: v for k, v in expect_passwords.items()}
        self.cancelled_callback = cancelled_callback
        self.job_timeout = job_timeout
        self.idle_timeout = idle_timeout
        self.extra_update_fields = extra_update_fields
        self.pexpect_timeout = pexpect_timeout
        self.proot_cmd = proot_cmd
        self.started_at = None

    @property
    def awx_playbook_path(self):
        return os.path.join(
            os.path.dirname(awx.__file__),
            'playbooks'
        )

    def path_to(self, *args):
        return os.path.join(self.private_data_dir, *args)

    def dispatch(self):
        '''
        Compile the playbook, its environment, and metadata into a series
        of files, and ship to a remote host for isolated execution.
        '''
        self.started_at = time.time()
        secrets = {
            'env': self.env.copy(),
            'passwords': self.expect_passwords,
            'ssh_key_data': None,
            'idle_timeout': self.idle_timeout,
            'job_timeout': self.job_timeout,
            'pexpect_timeout': self.pexpect_timeout
        }

        # if an ssh private key fifo exists, read its contents and delete it
        if self.ssh_key_path:
            buff = cStringIO.StringIO()
            with open(self.ssh_key_path, 'r') as fifo:
                for line in fifo:
                    buff.write(line)
            secrets['ssh_key_data'] = buff.getvalue()
            os.remove(self.ssh_key_path)

        # strip some environment variables that aren't applicable to isolated
        # execution
        for var in (
                'HOME', 'RABBITMQ_HOST', 'RABBITMQ_PASS', 'RABBITMQ_USER', 'CACHE',
                'DJANGO_PROJECT_DIR', 'DJANGO_SETTINGS_MODULE', 'RABBITMQ_VHOST'):
            secrets['env'].pop(var, None)
        self.build_isolated_job_data()

        extra_vars = {
            'src': self.private_data_dir,
            'dest': os.path.split(self.private_data_dir)[0],
        }
        if self.proot_temp_dir:
            extra_vars['proot_temp_dir'] = self.proot_temp_dir

        # Run ansible-playbook to launch a job on the isolated host.  This:
        #
        # - sets up a temporary directory for proot/bwrap (if necessary)
        # - copies encrypted job data from the controlling host to the isolated host (with rsync)
        # - writes the encryption secret to a named pipe on the isolated host
        # - launches the isolated playbook runner via `tower-expect start <job-id>`
        args = ['ansible-playbook', '-u', settings.AWX_ISOLATED_USERNAME, '-i',
                '%s,' % self.host, 'run_isolated.yml', '-e',
                json.dumps(extra_vars)]
        if self.instance.verbosity:
            args.append('-%s' % ('v' * min(5, self.instance.verbosity)))
        buff = StringIO.StringIO()
        logger.debug('Starting job on isolated host with `run_isolated.yml` playbook.')
        status, rc = run.run_pexpect(
            args, self.awx_playbook_path, self.env, buff,
            expect_passwords={
                re.compile(r'Secret:\s*?$', re.M): base64.b64encode(json.dumps(secrets))
            },
            idle_timeout=self.idle_timeout,
            job_timeout=settings.AWX_ISOLATED_LAUNCH_TIMEOUT,
            pexpect_timeout=5
        )
        if status != 'successful':
            self.stdout_handle.write(buff.getvalue())
        return status, rc

    def build_isolated_job_data(self):
        '''
        Write the playbook and metadata into a collection of files on the local
        file system.

        This function is intended to be used to compile job data so that it
        can be shipped to a remote, isolated host (via ssh).
        '''

        rsync_exclude = [
            # don't rsync source control metadata (it can be huge!)
            '- /project/.git',
            '- /project/.svn',
            '- /project/.hg',
            # don't rsync job events that are in the process of being written
            '- /artifacts/job_events/*-partial.json.tmp'
        ]

        for filename, data in (
            ['.rsync-filter', '\n'.join(rsync_exclude)],
            ['args', json.dumps(self.args)]
        ):
            path = self.path_to(filename)
            with open(path, 'w') as f:
                f.write(data)
            os.chmod(path, stat.S_IRUSR)

        # symlink the scm checkout (if there is one) so that it's rsync'ed over, too
        if 'AD_HOC_COMMAND_ID' not in self.env:
            os.symlink(self.cwd, self.path_to('project'))

        # create directories for build artifacts to live in
        os.makedirs(self.path_to('artifacts', 'job_events'), mode=stat.S_IRUSR | stat.S_IWUSR)

    def _missing_artifacts(self, path_list, buff):
        missing_artifacts = filter(lambda path: not os.path.exists(path), path_list)
        for path in missing_artifacts:
            self.stdout_handle.write('ansible did not exit cleanly, missing `{}`.\n'.format(path))
        if missing_artifacts:
            daemon_path = self.path_to('artifacts', 'daemon.log')
            if os.path.exists(daemon_path):
                # If available, show log files from the run.py call
                with codecs.open(daemon_path, 'r', encoding='utf-8') as f:
                    self.stdout_handle.write(f.read())
            else:
                # Provide the management playbook standard out if not available
                self.stdout_handle.write(buff.getvalue())
            return True
        return False

    def check(self, interval=None):
        """
        Repeatedly poll the isolated node to determine if the job has run.

        On success, copy job artifacts to the controlling node.
        On failure, continue to poll the isolated node (until the job timeout
        is exceeded).

        For a completed job run, this function returns (status, rc),
        representing the status and return code of the isolated
        `ansible-playbook` run.

        :param interval: an interval (in seconds) to wait between status polls
        """
        interval = interval if interval is not None else settings.AWX_ISOLATED_CHECK_INTERVAL
        extra_vars = {'src': self.private_data_dir}
        args = ['ansible-playbook', '-u', settings.AWX_ISOLATED_USERNAME, '-i',
                '%s,' % self.host, 'check_isolated.yml', '-e',
                json.dumps(extra_vars)]
        if self.instance.verbosity:
            args.append('-%s' % ('v' * min(5, self.instance.verbosity)))

        status = 'failed'
        rc = None
        buff = cStringIO.StringIO()
        last_check = time.time()
        seek = 0
        job_timeout = remaining = self.job_timeout
        while status == 'failed':
            if job_timeout != 0:
                remaining = max(0, job_timeout - (time.time() - self.started_at))
                if remaining == 0:
                    # if it takes longer than $REMAINING_JOB_TIMEOUT to retrieve
                    # job artifacts from the host, consider the job failed
                    if isinstance(self.extra_update_fields, dict):
                        self.extra_update_fields['job_explanation'] = "Job terminated due to timeout"
                    status = 'failed'
                    break

            canceled = self.cancelled_callback() if self.cancelled_callback else False
            if not canceled and time.time() - last_check < interval:
                # If the job isn't cancelled, but we haven't waited `interval` seconds, wait longer
                time.sleep(1)
                continue

            buff = cStringIO.StringIO()
            logger.debug('Checking job on isolated host with `check_isolated.yml` playbook.')
            status, rc = run.run_pexpect(
                args, self.awx_playbook_path, self.env, buff,
                cancelled_callback=self.cancelled_callback,
                idle_timeout=remaining,
                job_timeout=remaining,
                pexpect_timeout=5,
                proot_cmd=self.proot_cmd
            )

            path = self.path_to('artifacts', 'stdout')
            if os.path.exists(path):
                with codecs.open(path, 'r', encoding='utf-8') as f:
                    f.seek(seek)
                    for line in f:
                        self.stdout_handle.write(line)
                        seek += len(line)

            last_check = time.time()

        if status == 'successful':
            status_path = self.path_to('artifacts', 'status')
            rc_path = self.path_to('artifacts', 'rc')
            if self._missing_artifacts([status_path, rc_path], buff):
                status = 'failed'
                rc = 1
            else:
                with open(status_path, 'r') as f:
                    status = f.readline()
                with open(rc_path, 'r') as f:
                    rc = int(f.readline())
        elif status == 'failed':
            # if we were unable to retrieve job reults from the isolated host,
            # print stdout of the `check_isolated.yml` playbook for clues
            self.stdout_handle.write(buff.getvalue())

        return status, rc

    def cleanup(self):
        # If the job failed for any reason, make a last-ditch effort at cleanup
        extra_vars = {
            'private_data_dir': self.private_data_dir,
            'cleanup_dirs': [
                self.private_data_dir,
                self.proot_temp_dir,
            ],
        }
        args = ['ansible-playbook', '-u', settings.AWX_ISOLATED_USERNAME, '-i',
                '%s,' % self.host, 'clean_isolated.yml', '-e',
                json.dumps(extra_vars)]
        logger.debug('Cleaning up job on isolated host with `clean_isolated.yml` playbook.')
        buff = cStringIO.StringIO()
        status, rc = run.run_pexpect(
            args, self.awx_playbook_path, self.env, buff,
            idle_timeout=60, job_timeout=60,
            pexpect_timeout=5
        )

        if status != 'successful':
            # stdout_handle is closed by this point so writing output to logs is our only option
            logger.warning('Cleanup from isolated job encountered error, output:\n{}'.format(buff.getvalue()))

    @staticmethod
    def wrap_stdout_handle(instance, private_data_dir, stdout_handle):
        dispatcher = CallbackQueueDispatcher()

        def job_event_callback(event_data):
            event_data.setdefault('job_id', instance.id)
            if 'uuid' in event_data:
                filename = '{}-partial.json'.format(event_data['uuid'])
                partial_filename = os.path.join(private_data_dir, 'artifacts', 'job_events', filename)
                try:
                    with codecs.open(partial_filename, 'r', encoding='utf-8') as f:
                        partial_event_data = json.load(f)
                    event_data.update(partial_event_data)
                except IOError:
                    if event_data.get('event', '') != 'verbose':
                        logger.error('Missing callback data for event type `{}`, uuid {}, job {}.\nevent_data: {}'.format(
                            event_data.get('event', ''), event_data['uuid'], instance.id, event_data))
            dispatcher.dispatch(event_data)

        return OutputEventFilter(stdout_handle, job_event_callback)

    def run(self, instance, host, private_data_dir, proot_temp_dir):
        """
        Run a job on an isolated host.

        :param instance:         a `model.Job` instance
        :param host:             the hostname (or IP address) to run the
                                 isolated job on
        :param private_data_dir: an absolute path on the local file system
                                 where job-specific data should be written
                                 (i.e., `/tmp/ansible_tower_xyz/`)
        :param proot_temp_dir:   a temporary directory which bwrap maps
                                 restricted paths to

        For a completed job run, this function returns (status, rc),
        representing the status and return code of the isolated
        `ansible-playbook` run.
        """
        self.instance = instance
        self.host = host
        self.private_data_dir = private_data_dir
        self.proot_temp_dir = proot_temp_dir
        status, rc = self.dispatch()
        if status == 'successful':
            status, rc = self.check()
        else:
            # If dispatch fails, attempt to consume artifacts that *might* exist
            self.check()
        self.cleanup()
        return status, rc

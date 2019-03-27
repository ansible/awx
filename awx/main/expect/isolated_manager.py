import json
import os
import shutil
import stat
import tempfile
import time
import logging
from io import StringIO

from django.conf import settings

import awx
from awx.main.expect import run
from awx.main.utils import get_system_task_capacity
from awx.main.queue import CallbackQueueDispatcher

logger = logging.getLogger('awx.isolated.manager')
playbook_logger = logging.getLogger('awx.isolated.manager.playbooks')


class IsolatedManager(object):

    def __init__(self, env, cancelled_callback=None, job_timeout=0,
                 idle_timeout=None):
        """
        :param env:                 a dict containing environment variables for the
                                    subprocess, ala `os.environ`
        :param cancelled_callback:  a callable - which returns `True` or `False`
                                    - signifying if the job has been prematurely
                                      cancelled
        :param job_timeout          a timeout (in seconds); if the total job runtime
                                    exceeds this, the process will be killed
        :param idle_timeout         a timeout (in seconds); if new output is not
                                    sent to stdout in this interval, the process
                                    will be terminated
        """
        self.management_env = self._base_management_env()
        self.cancelled_callback = cancelled_callback
        self.job_timeout = job_timeout
        self.idle_timeout = idle_timeout
        self.started_at = None

    @staticmethod
    def _base_management_env():
        '''
        Returns environment variables to use when running a playbook
        that manages the isolated instance.
        Use of normal job callback and other such configurations are avoided.
        '''
        env = dict(os.environ.items())
        env['ANSIBLE_RETRY_FILES_ENABLED'] = 'False'
        env['ANSIBLE_HOST_KEY_CHECKING'] = 'False'
        env['ANSIBLE_LIBRARY'] = os.path.join(os.path.dirname(awx.__file__), 'plugins', 'isolated')
        return env

    @staticmethod
    def _build_args(playbook, hosts, extra_vars=None):
        '''
        Returns list of Ansible CLI command arguments for a management task

        :param playbook:   name of the playbook to run
        :param hosts:      host pattern to operate on, ex. "localhost,"
        :param extra_vars: optional dictionary of extra_vars to apply
        '''
        args = [
            'ansible-playbook',
            playbook,
            '-u', settings.AWX_ISOLATED_USERNAME,
            '-T', str(settings.AWX_ISOLATED_CONNECTION_TIMEOUT),
            '-i', hosts
        ]
        if extra_vars:
            args.extend(['-e', json.dumps(extra_vars)])
        if settings.AWX_ISOLATED_VERBOSITY:
            args.append('-%s' % ('v' * min(5, settings.AWX_ISOLATED_VERBOSITY)))
        return args

    @classmethod
    def awx_playbook_path(cls):
        return os.path.abspath(os.path.join(
            os.path.dirname(awx.__file__),
            'playbooks'
        ))

    def path_to(self, *args):
        return os.path.join(self.private_data_dir, *args)

    def dispatch(self, playbook=None, module=None, module_args=None):
        '''
        Ship the runner payload to a remote host for isolated execution.
        '''
        self.handled_events = set()
        self.started_at = time.time()

        self.build_isolated_job_data()
        extra_vars = {
            'src': self.private_data_dir,
            'dest': settings.AWX_PROOT_BASE_PATH,
            'ident': self.ident
        }
        if playbook:
            extra_vars['playbook'] = playbook
        if module and module_args:
            extra_vars['module'] = module
            extra_vars['module_args'] = module_args

        # Run ansible-playbook to launch a job on the isolated host.  This:
        #
        # - sets up a temporary directory for proot/bwrap (if necessary)
        # - copies encrypted job data from the controlling host to the isolated host (with rsync)
        # - writes the encryption secret to a named pipe on the isolated host
        # - launches ansible-runner
        args = self._build_args('run_isolated.yml', '%s,' % self.host, extra_vars)
        if self.instance.verbosity:
            args.append('-%s' % ('v' * min(5, self.instance.verbosity)))
        buff = StringIO()
        logger.debug('Starting job {} on isolated host with `run_isolated.yml` playbook.'.format(self.instance.id))
        status, rc = IsolatedManager.run_pexpect(
            args, self.awx_playbook_path(), self.management_env, buff,
            idle_timeout=self.idle_timeout,
            job_timeout=settings.AWX_ISOLATED_LAUNCH_TIMEOUT,
            pexpect_timeout=5
        )
        output = buff.getvalue()
        playbook_logger.info('Isolated job {} dispatch:\n{}'.format(self.instance.id, output))
        if status != 'successful':
            for event_data in [
                {'event': 'verbose', 'stdout': output},
                {'event': 'EOF', 'final_counter': 1},
            ]:
                event_data.setdefault(self.event_data_key, self.instance.id)
                CallbackQueueDispatcher().dispatch(event_data)
        return status, rc

    @classmethod
    def run_pexpect(cls, pexpect_args, *args, **kw):
        isolated_ssh_path = None
        try:
            if all([
                getattr(settings, 'AWX_ISOLATED_KEY_GENERATION', False) is True,
                getattr(settings, 'AWX_ISOLATED_PRIVATE_KEY', None)
            ]):
                isolated_ssh_path = tempfile.mkdtemp(prefix='awx_isolated', dir=settings.AWX_PROOT_BASE_PATH)
                os.chmod(isolated_ssh_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
                isolated_key = os.path.join(isolated_ssh_path, '.isolated')
                ssh_sock = os.path.join(isolated_ssh_path, '.isolated_ssh_auth.sock')
                run.open_fifo_write(isolated_key, settings.AWX_ISOLATED_PRIVATE_KEY)
                pexpect_args = run.wrap_args_with_ssh_agent(pexpect_args, isolated_key, ssh_sock, silence_ssh_add=True)
            return run.run_pexpect(pexpect_args, *args, **kw)
        finally:
            if isolated_ssh_path:
                shutil.rmtree(isolated_ssh_path)

    def build_isolated_job_data(self):
        '''
        Write metadata related to the playbook run into a collection of files
        on the local file system.
        '''

        rsync_exclude = [
            # don't rsync source control metadata (it can be huge!)
            '- /project/.git',
            '- /project/.svn',
            '- /project/.hg',
            # don't rsync job events that are in the process of being written
            '- /artifacts/job_events/*-partial.json.tmp',
            # don't rsync the ssh_key FIFO
            '- /env/ssh_key',
        ]

        for filename, data in (
            ['.rsync-filter', '\n'.join(rsync_exclude)],
        ):
            path = self.path_to(filename)
            with open(path, 'w') as f:
                f.write(data)
            os.chmod(path, stat.S_IRUSR)

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
        args = self._build_args('check_isolated.yml', '%s,' % self.host, extra_vars)
        if self.instance.verbosity:
            args.append('-%s' % ('v' * min(5, self.instance.verbosity)))

        status = 'failed'
        output = ''
        rc = None
        buff = StringIO()
        last_check = time.time()
        job_timeout = remaining = self.job_timeout
        dispatcher = CallbackQueueDispatcher()
        while status == 'failed':
            if job_timeout != 0:
                remaining = max(0, job_timeout - (time.time() - self.started_at))

            canceled = self.cancelled_callback() if self.cancelled_callback else False
            if not canceled and time.time() - last_check < interval:
                # If the job isn't cancelled, but we haven't waited `interval` seconds, wait longer
                time.sleep(1)
                continue

            if canceled:
                logger.warning('Isolated job {} was manually cancelled.'.format(self.instance.id))

            buff = StringIO()
            logger.debug('Checking on isolated job {} with `check_isolated.yml`.'.format(self.instance.id))
            status, rc = IsolatedManager.run_pexpect(
                args, self.awx_playbook_path(), self.management_env, buff,
                cancelled_callback=self.cancelled_callback,
                idle_timeout=remaining,
                job_timeout=remaining,
                pexpect_timeout=5,
                proot_cmd='bwrap'
            )
            output = buff.getvalue().encode('utf-8')
            playbook_logger.info('Isolated job {} check:\n{}'.format(self.instance.id, output))

            # discover new events and ingest them
            events_path = self.path_to('artifacts', self.ident, 'job_events')

            # it's possible that `events_path` doesn't exist *yet*, because runner
            # hasn't actually written any events yet (if you ran e.g., a sleep 30)
            # only attempt to consume events if any were rsynced back
            if os.path.exists(events_path):
                for event in set(os.listdir(events_path)) - self.handled_events:
                    path = os.path.join(events_path, event)
                    if os.path.exists(path):
                        event_data = json.load(
                            open(os.path.join(events_path, event), 'r')
                        )
                        event_data.setdefault(self.event_data_key, self.instance.id)
                        dispatcher.dispatch(event_data)
                        self.handled_events.add(event)

                        # handle artifacts
                        if event_data.get('event_data', {}).get('artifact_data', {}):
                            self.instance.artifacts = event_data['event_data']['artifact_data']
                            self.instance.save(update_fields=['artifacts'])

            last_check = time.time()

        if status == 'successful':
            status_path = self.path_to('artifacts', self.ident, 'status')
            rc_path = self.path_to('artifacts', self.ident, 'rc')
            with open(status_path, 'r') as f:
                status = f.readline()
            with open(rc_path, 'r') as f:
                rc = int(f.readline())

        # emit an EOF event
        event_data = {
            'event': 'EOF',
            'final_counter': len(self.handled_events)
        }
        event_data.setdefault(self.event_data_key, self.instance.id)
        dispatcher.dispatch(event_data)

        return status, rc

    def cleanup(self):
        # If the job failed for any reason, make a last-ditch effort at cleanup
        extra_vars = {
            'private_data_dir': self.private_data_dir,
            'cleanup_dirs': [
                self.private_data_dir,
            ],
        }
        args = self._build_args('clean_isolated.yml', '%s,' % self.host, extra_vars)
        logger.debug('Cleaning up job {} on isolated host with `clean_isolated.yml` playbook.'.format(self.instance.id))
        buff = StringIO()
        timeout = max(60, 2 * settings.AWX_ISOLATED_CONNECTION_TIMEOUT)
        status, rc = IsolatedManager.run_pexpect(
            args, self.awx_playbook_path(), self.management_env, buff,
            idle_timeout=timeout, job_timeout=timeout,
            pexpect_timeout=5
        )
        output = buff.getvalue().encode('utf-8')
        playbook_logger.info('Isolated job {} cleanup:\n{}'.format(self.instance.id, output))

        if status != 'successful':
            # stdout_handle is closed by this point so writing output to logs is our only option
            logger.warning('Isolated job {} cleanup error, output:\n{}'.format(self.instance.id, output))

    @classmethod
    def update_capacity(cls, instance, task_result, awx_application_version):
        instance.version = 'ansible-runner-{}'.format(task_result['version'])

        if instance.capacity == 0 and task_result['capacity_cpu']:
            logger.warning('Isolated instance {} has re-joined.'.format(instance.hostname))
        instance.cpu_capacity = int(task_result['capacity_cpu'])
        instance.mem_capacity = int(task_result['capacity_mem'])
        instance.capacity = get_system_task_capacity(scale=instance.capacity_adjustment,
                                                     cpu_capacity=int(task_result['capacity_cpu']),
                                                     mem_capacity=int(task_result['capacity_mem']))
        instance.save(update_fields=['cpu_capacity', 'mem_capacity', 'capacity', 'version', 'modified'])

    @classmethod
    def health_check(cls, instance_qs, awx_application_version):
        '''
        :param instance_qs:         List of Django objects representing the
                                    isolated instances to manage
        Runs playbook that will
         - determine if instance is reachable
         - find the instance capacity
         - clean up orphaned private files
        Performs save on each instance to update its capacity.
        '''
        hostname_string = ''
        for instance in instance_qs:
            hostname_string += '{},'.format(instance.hostname)
        args = cls._build_args('heartbeat_isolated.yml', hostname_string)
        args.extend(['--forks', str(len(instance_qs))])
        env = cls._base_management_env()

        try:
            facts_path = tempfile.mkdtemp()
            env['ANSIBLE_CACHE_PLUGIN'] = 'jsonfile'
            env['ANSIBLE_CACHE_PLUGIN_CONNECTION'] = facts_path

            buff = StringIO()
            timeout = max(60, 2 * settings.AWX_ISOLATED_CONNECTION_TIMEOUT)
            status, rc = IsolatedManager.run_pexpect(
                args, cls.awx_playbook_path(), env, buff,
                idle_timeout=timeout, job_timeout=timeout,
                pexpect_timeout=5
            )
            heartbeat_stdout = buff.getvalue().encode('utf-8')
            buff.close()

            for instance in instance_qs:
                output = heartbeat_stdout
                task_result = {}
                try:
                    with open(os.path.join(facts_path, instance.hostname), 'r') as facts_data:
                        output = facts_data.read()
                    task_result = json.loads(output)
                except Exception:
                    logger.exception('Failed to read status from isolated instances, output:\n {}'.format(output))
                if 'awx_capacity_cpu' in task_result and 'awx_capacity_mem' in task_result:
                    task_result = {
                        'capacity_cpu': task_result['awx_capacity_cpu'],
                        'capacity_mem': task_result['awx_capacity_mem'],
                        'version': task_result['awx_capacity_version']
                    }
                    cls.update_capacity(instance, task_result, awx_application_version)
                    logger.debug('Isolated instance {} successful heartbeat'.format(instance.hostname))
                elif instance.capacity == 0:
                    logger.debug('Isolated instance {} previously marked as lost, could not re-join.'.format(
                        instance.hostname))
                else:
                    logger.warning('Could not update status of isolated instance {}'.format(instance.hostname))
                    if instance.is_lost(isolated=True):
                        instance.capacity = 0
                        instance.save(update_fields=['capacity'])
                        logger.error('Isolated instance {} last checked in at {}, marked as lost.'.format(
                            instance.hostname, instance.modified))
        finally:
            if os.path.exists(facts_path):
                shutil.rmtree(facts_path)

    def run(self, instance, private_data_dir, playbook, module, module_args,
            event_data_key, ident=None):
        """
        Run a job on an isolated host.

        :param instance:         a `model.Job` instance
        :param private_data_dir: an absolute path on the local file system
                                 where job-specific data should be written
                                 (i.e., `/tmp/ansible_awx_xyz/`)
        :param playbook:         the playbook to run
        :param module:           the module to run
        :param module_args:      the module args to use
        :param event_data_key:   e.g., job_id, inventory_id, ...

        For a completed job run, this function returns (status, rc),
        representing the status and return code of the isolated
        `ansible-playbook` run.
        """
        self.ident = ident
        self.event_data_key = event_data_key
        self.instance = instance
        self.host = instance.execution_node
        self.private_data_dir = private_data_dir
        status, rc = self.dispatch(playbook, module, module_args)
        if status == 'successful':
            status, rc = self.check()
        self.cleanup()
        return status, rc

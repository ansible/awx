import json
import os
import shutil
import stat
import tempfile
import time
import logging

from django.conf import settings
import ansible_runner

import awx
from awx.main.utils import get_system_task_capacity
from awx.main.queue import CallbackQueueDispatcher

logger = logging.getLogger('awx.isolated.manager')
playbook_logger = logging.getLogger('awx.isolated.manager.playbooks')


class IsolatedManager(object):

    def __init__(self, cancelled_callback=None, idle_timeout=None):
        """
        :param cancelled_callback:  a callable - which returns `True` or `False`
                                    - signifying if the job has been prematurely
                                      cancelled
        :param idle_timeout         a timeout (in seconds); if new output is not
                                    sent to stdout in this interval, the process
                                    will be terminated
        """
        self.cancelled_callback = cancelled_callback
        self.idle_timeout = idle_timeout or max(60, 2 * settings.AWX_ISOLATED_CONNECTION_TIMEOUT)
        self.started_at = None

    def build_runner_params(self, hosts, verbosity=1):
        env = dict(os.environ.items())
        env['ANSIBLE_RETRY_FILES_ENABLED'] = 'False'
        env['ANSIBLE_HOST_KEY_CHECKING'] = 'False'
        env['ANSIBLE_LIBRARY'] = os.path.join(os.path.dirname(awx.__file__), 'plugins', 'isolated')

        def finished_callback(runner_obj):
            if runner_obj.status == 'failed':
                stdout = runner_obj.stdout.read()
                playbook_logger.error(stdout)
                event_data = {'event': 'verbose', 'stdout': stdout, self.event_data_key: self.instance.id}
                CallbackQueueDispatcher().dispatch(event_data)
            else:
                playbook_logger.info(runner_obj.stdout.read())

        inventory = '\n'.join([
            '{} ansible_ssh_user={}'.format(host, settings.AWX_ISOLATED_USERNAME)
            for host in hosts
        ])

        return {
            'project_dir': os.path.abspath(os.path.join(
                os.path.dirname(awx.__file__),
                'playbooks'
            )),
            'inventory': inventory,
            'envvars': env,
            'finished_callback': finished_callback,
            'verbosity': verbosity,
            'cancel_callback': self.cancelled_callback,
            'settings': {
                'idle_timeout': self.idle_timeout,
                'job_timeout': settings.AWX_ISOLATED_LAUNCH_TIMEOUT,
                'pexpect_timeout': getattr(settings, 'PEXPECT_TIMEOUT', 5),
            },
        }

    def path_to(self, *args):
        return os.path.join(self.private_data_dir, *args)

    def run_management_playbook(self, playbook, private_data_dir, **kw):
        iso_dir = tempfile.mkdtemp(
            prefix=playbook,
            dir=private_data_dir
        )
        params = self.runner_params.copy()
        params['playbook'] = playbook
        params['private_data_dir'] = iso_dir
        params.update(**kw)
        if all([
            getattr(settings, 'AWX_ISOLATED_KEY_GENERATION', False) is True,
            getattr(settings, 'AWX_ISOLATED_PRIVATE_KEY', None)
        ]):
            params['ssh_key'] = settings.AWX_ISOLATED_PRIVATE_KEY
        return ansible_runner.interface.run(**params)

    def dispatch(self, playbook=None, module=None, module_args=None):
        '''
        Ship the runner payload to a remote host for isolated execution.
        '''
        self.handled_events = set()
        self.started_at = time.time()

        # exclude certain files from the rsync
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

        extravars = {
            'src': self.private_data_dir,
            'dest': settings.AWX_PROOT_BASE_PATH,
            'ident': self.ident
        }
        if playbook:
            extravars['playbook'] = playbook
        if module and module_args:
            extravars['module'] = module
            extravars['module_args'] = module_args

        logger.debug('Starting job {} on isolated host with `run_isolated.yml` playbook.'.format(self.instance.id))
        runner_obj = self.run_management_playbook('run_isolated.yml',
                                                  self.private_data_dir,
                                                  extravars=extravars)
        return runner_obj.status, runner_obj.rc

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
        extravars = {'src': self.private_data_dir}
        status = 'failed'
        rc = None
        last_check = time.time()
        dispatcher = CallbackQueueDispatcher()
        while status == 'failed':
            canceled = self.cancelled_callback() if self.cancelled_callback else False
            if not canceled and time.time() - last_check < interval:
                # If the job isn't cancelled, but we haven't waited `interval` seconds, wait longer
                time.sleep(1)
                continue

            if canceled:
                logger.warning('Isolated job {} was manually cancelled.'.format(self.instance.id))

            logger.debug('Checking on isolated job {} with `check_isolated.yml`.'.format(self.instance.id))
            runner_obj = self.run_management_playbook('check_isolated.yml',
                                                      self.private_data_dir,
                                                      extravars=extravars)
            status, rc = runner_obj.status, runner_obj.rc

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
        extravars = {
            'private_data_dir': self.private_data_dir,
            'cleanup_dirs': [
                self.private_data_dir,
            ],
        }
        logger.debug('Cleaning up job {} on isolated host with `clean_isolated.yml` playbook.'.format(self.instance.id))
        self.run_management_playbook(
            'clean_isolated.yml',
            self.private_data_dir,
            extravars=extravars
        )

    @classmethod
    def update_capacity(cls, instance, task_result):
        instance.version = 'ansible-runner-{}'.format(task_result['version'])

        if instance.capacity == 0 and task_result['capacity_cpu']:
            logger.warning('Isolated instance {} has re-joined.'.format(instance.hostname))
        instance.cpu_capacity = int(task_result['capacity_cpu'])
        instance.mem_capacity = int(task_result['capacity_mem'])
        instance.capacity = get_system_task_capacity(scale=instance.capacity_adjustment,
                                                     cpu_capacity=int(task_result['capacity_cpu']),
                                                     mem_capacity=int(task_result['capacity_mem']))
        instance.save(update_fields=['cpu_capacity', 'mem_capacity', 'capacity', 'version', 'modified'])

    def health_check(self, instance_qs):
        '''
        :param instance_qs:         List of Django objects representing the
                                    isolated instances to manage
        Runs playbook that will
         - determine if instance is reachable
         - find the instance capacity
         - clean up orphaned private files
        Performs save on each instance to update its capacity.
        '''
        # TODO: runner doesn't have a --forks arg
        #args.extend(['--forks', str(len(instance_qs))])

        try:
            private_data_dir = tempfile.mkdtemp(
                prefix='awx_iso_heartbeat_',
                dir=settings.AWX_PROOT_BASE_PATH
            )
            self.runner_params = self.build_runner_params([
                instance.hostname for instance in instance_qs
            ])
            self.runner_params['private_data_dir'] = private_data_dir
            runner_obj = self.run_management_playbook(
                'heartbeat_isolated.yml',
                private_data_dir
            )

            if runner_obj.status == 'successful':
                for instance in instance_qs:
                    task_result = {}
                    try:
                        task_result = runner_obj.get_fact_cache(instance.hostname)
                    except Exception:
                        logger.exception('Failed to read status from isolated instances')
                    if 'awx_capacity_cpu' in task_result and 'awx_capacity_mem' in task_result:
                        task_result = {
                            'capacity_cpu': task_result['awx_capacity_cpu'],
                            'capacity_mem': task_result['awx_capacity_mem'],
                            'version': task_result['awx_capacity_version']
                        }
                        IsolatedManager.update_capacity(instance, task_result)
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
            if os.path.exists(private_data_dir):
                shutil.rmtree(private_data_dir)

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
        self.private_data_dir = private_data_dir
        self.runner_params = self.build_runner_params(
            [instance.execution_node],
            verbosity=min(5, self.instance.verbosity)
        )
        status, rc = self.dispatch(playbook, module, module_args)
        if status == 'successful':
            status, rc = self.check()
        self.cleanup()
        return status, rc

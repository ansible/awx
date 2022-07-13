import json
import time
import logging
from collections import deque
import os
import stat

# Django
from django.utils.timezone import now
from django.conf import settings
from django_guid import get_guid
from django.utils.functional import cached_property

# AWX
from awx.main.redact import UriCleaner
from awx.main.constants import MINIMAL_EVENTS, ANSIBLE_RUNNER_NEEDS_UPDATE_MESSAGE
from awx.main.utils.update_model import update_model
from awx.main.queue import CallbackQueueDispatcher
from awx.main.tasks.signals import signal_callback

logger = logging.getLogger('awx.main.tasks.callback')


class RunnerCallback:
    def __init__(self, model=None):
        self.parent_workflow_job_id = None
        self.host_map = {}
        self.guid = get_guid()
        self.job_created = None
        self.recent_event_timings = deque(maxlen=settings.MAX_WEBSOCKET_EVENT_RATE)
        self.dispatcher = CallbackQueueDispatcher()
        self.safe_env = {}
        self.event_ct = 0
        self.model = model
        self.update_attempts = int(settings.DISPATCHER_DB_DOWNTOWN_TOLLERANCE / 5)
        self.wrapup_event_dispatched = False
        self.extra_update_fields = {}

    def update_model(self, pk, _attempt=0, **updates):
        return update_model(self.model, pk, _attempt=0, _max_attempts=self.update_attempts, **updates)

    @cached_property
    def wrapup_event_type(self):
        return self.instance.event_class.WRAPUP_EVENT

    @cached_property
    def event_data_key(self):
        return self.instance.event_class.JOB_REFERENCE

    def delay_update(self, skip_if_already_set=False, **kwargs):
        """Stash fields that should be saved along with the job status change"""
        for key, value in kwargs.items():
            if key in self.extra_update_fields and skip_if_already_set:
                continue
            elif key in self.extra_update_fields and key in ('job_explanation', 'result_traceback'):
                if str(value) in self.extra_update_fields.get(key, ''):
                    continue  # if already set, avoid duplicating messages
                # In the case of these fields, we do not want to lose any prior information, so combine values
                self.extra_update_fields[key] = '\n'.join([str(self.extra_update_fields[key]), str(value)])
            else:
                self.extra_update_fields[key] = value

    def get_delayed_update_fields(self):
        """Return finalized dict of all fields that should be saved along with the job status change"""
        self.extra_update_fields['emitted_events'] = self.event_ct
        if 'got an unexpected keyword argument' in self.extra_update_fields.get('result_traceback', ''):
            self.delay_update(result_traceback=ANSIBLE_RUNNER_NEEDS_UPDATE_MESSAGE)
        return self.extra_update_fields

    def event_handler(self, event_data):
        #
        # ⚠️  D-D-D-DANGER ZONE ⚠️
        # This method is called once for *every event* emitted by Ansible
        # Runner as a playbook runs.  That means that changes to the code in
        # this method are _very_ likely to introduce performance regressions.
        #
        # Even if this function is made on average .05s slower, it can have
        # devastating performance implications for playbooks that emit
        # tens or hundreds of thousands of events.
        #
        # Proceed with caution!
        #
        """
        Ansible runner puts a parent_uuid on each event, no matter what the type.
        AWX only saves the parent_uuid if the event is for a Job.
        """
        # cache end_line locally for RunInventoryUpdate tasks
        # which generate job events from two 'streams':
        # ansible-inventory and the awx.main.commands.inventory_import
        # logger

        if event_data.get(self.event_data_key, None):
            if self.event_data_key != 'job_id':
                event_data.pop('parent_uuid', None)
        if self.parent_workflow_job_id:
            event_data['workflow_job_id'] = self.parent_workflow_job_id
        event_data['job_created'] = self.job_created
        if self.host_map:
            host = event_data.get('event_data', {}).get('host', '').strip()
            if host:
                event_data['host_name'] = host
                if host in self.host_map:
                    event_data['host_id'] = self.host_map[host]
            else:
                event_data['host_name'] = ''
                event_data['host_id'] = ''
            if event_data.get('event') == 'playbook_on_stats':
                event_data['host_map'] = self.host_map

        if isinstance(self, RunnerCallbackForProjectUpdate):
            # need a better way to have this check.
            # it's common for Ansible's SCM modules to print
            # error messages on failure that contain the plaintext
            # basic auth credentials (username + password)
            # it's also common for the nested event data itself (['res']['...'])
            # to contain unredacted text on failure
            # this is a _little_ expensive to filter
            # with regex, but project updates don't have many events,
            # so it *should* have a negligible performance impact
            task = event_data.get('event_data', {}).get('task_action')
            try:
                if task in ('git', 'svn'):
                    event_data_json = json.dumps(event_data)
                    event_data_json = UriCleaner.remove_sensitive(event_data_json)
                    event_data = json.loads(event_data_json)
            except json.JSONDecodeError:
                pass

        if 'event_data' in event_data:
            event_data['event_data']['guid'] = self.guid

        # To prevent overwhelming the broadcast queue, skip some websocket messages
        if self.recent_event_timings:
            cpu_time = time.time()
            first_window_time = self.recent_event_timings[0]
            last_window_time = self.recent_event_timings[-1]

            if event_data.get('event') in MINIMAL_EVENTS:
                should_emit = True  # always send some types like playbook_on_stats
            elif event_data.get('stdout') == '' and event_data['start_line'] == event_data['end_line']:
                should_emit = False  # exclude events with no output
            else:
                should_emit = any(
                    [
                        # if 30the most recent websocket message was sent over 1 second ago
                        cpu_time - first_window_time > 1.0,
                        # if the very last websocket message came in over 1/30 seconds ago
                        self.recent_event_timings.maxlen * (cpu_time - last_window_time) > 1.0,
                        # if the queue is not yet full
                        len(self.recent_event_timings) != self.recent_event_timings.maxlen,
                    ]
                )

            if should_emit:
                self.recent_event_timings.append(cpu_time)
            else:
                event_data.setdefault('event_data', {})
                event_data['skip_websocket_message'] = True

        elif self.recent_event_timings.maxlen:
            self.recent_event_timings.append(time.time())

        if event_data.get('event', '') == self.wrapup_event_type:
            self.wrapup_event_dispatched = True

        event_data.setdefault(self.event_data_key, self.instance.id)
        self.dispatcher.dispatch(event_data)
        self.event_ct += 1

        '''
        Handle artifacts
        '''
        if event_data.get('event_data', {}).get('artifact_data', {}):
            self.delay_update(artifacts=event_data['event_data']['artifact_data'])

        return False

    def cancel_callback(self):
        """
        Ansible runner callback to tell the job when/if it is canceled
        """
        unified_job_id = self.instance.pk
        if signal_callback():
            return True
        try:
            self.instance = self.update_model(unified_job_id)
        except Exception:
            logger.exception(f'Encountered error during cancel check for {unified_job_id}, canceling now')
            return True
        if not self.instance:
            logger.error('unified job {} was deleted while running, canceling'.format(unified_job_id))
            return True
        if self.instance.cancel_flag or self.instance.status == 'canceled':
            cancel_wait = (now() - self.instance.modified).seconds if self.instance.modified else 0
            if cancel_wait > 5:
                logger.warning('Request to cancel {} took {} seconds to complete.'.format(self.instance.log_format, cancel_wait))
            return True
        return False

    def finished_callback(self, runner_obj):
        """
        Ansible runner callback triggered on finished run
        """
        event_data = {
            'event': 'EOF',
            'final_counter': self.event_ct,
            'guid': self.guid,
        }
        event_data.setdefault(self.event_data_key, self.instance.id)
        self.dispatcher.dispatch(event_data)
        if self.wrapup_event_type == 'EOF':
            self.wrapup_event_dispatched = True

    def status_handler(self, status_data, runner_config):
        """
        Ansible runner callback triggered on status transition
        """
        if status_data['status'] == 'starting':
            job_env = dict(runner_config.env)
            '''
            Take the safe environment variables and overwrite
            '''
            for k, v in self.safe_env.items():
                if k in job_env:
                    job_env[k] = v
            from awx.main.signals import disable_activity_stream  # Circular import

            with disable_activity_stream():
                self.instance = self.update_model(self.instance.pk, job_args=json.dumps(runner_config.command), job_cwd=runner_config.cwd, job_env=job_env)
        elif status_data['status'] == 'failed':
            # For encrypted ssh_key_data, ansible-runner worker will open and write the
            # ssh_key_data to a named pipe. Then, once the podman container starts, ssh-agent will
            # read from this named pipe so that the key can be used in ansible-playbook.
            # Once the podman container exits, the named pipe is deleted.
            # However, if the podman container fails to start in the first place, e.g. the image
            # name is incorrect, then this pipe is not cleaned up. Eventually ansible-runner
            # processor will attempt to write artifacts to the private data dir via unstream_dir, requiring
            # that it open this named pipe. This leads to a hang. Thus, before any artifacts
            # are written by the processor, it's important to remove this ssh_key_data pipe.
            private_data_dir = self.instance.job_env.get('AWX_PRIVATE_DATA_DIR', None)
            if private_data_dir:
                key_data_file = os.path.join(private_data_dir, 'artifacts', str(self.instance.id), 'ssh_key_data')
                if os.path.exists(key_data_file) and stat.S_ISFIFO(os.stat(key_data_file).st_mode):
                    os.remove(key_data_file)
        elif status_data['status'] == 'error':
            result_traceback = status_data.get('result_traceback', None)
            if result_traceback:
                self.delay_update(result_traceback=result_traceback)


class RunnerCallbackForProjectUpdate(RunnerCallback):
    def __init__(self, *args, **kwargs):
        super(RunnerCallbackForProjectUpdate, self).__init__(*args, **kwargs)
        self.playbook_new_revision = None
        self.host_map = {}

    def event_handler(self, event_data):
        super_return_value = super(RunnerCallbackForProjectUpdate, self).event_handler(event_data)
        returned_data = event_data.get('event_data', {})
        if returned_data.get('task_action', '') == 'set_fact':
            returned_facts = returned_data.get('res', {}).get('ansible_facts', {})
            if 'scm_version' in returned_facts:
                self.playbook_new_revision = returned_facts['scm_version']
        return super_return_value


class RunnerCallbackForInventoryUpdate(RunnerCallback):
    def __init__(self, *args, **kwargs):
        super(RunnerCallbackForInventoryUpdate, self).__init__(*args, **kwargs)
        self.end_line = 0

    def event_handler(self, event_data):
        self.end_line = event_data['end_line']

        return super(RunnerCallbackForInventoryUpdate, self).event_handler(event_data)


class RunnerCallbackForAdHocCommand(RunnerCallback):
    def __init__(self, *args, **kwargs):
        super(RunnerCallbackForAdHocCommand, self).__init__(*args, **kwargs)
        self.host_map = {}


class RunnerCallbackForSystemJob(RunnerCallback):

    pass

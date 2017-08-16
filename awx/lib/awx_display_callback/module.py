# Copyright (c) 2016 Ansible by Red Hat, Inc.
#
# This file is part of Ansible Tower, but depends on code imported from Ansible.
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import (absolute_import, division, print_function)

# Python
import contextlib
import sys
import uuid
from copy import copy

# Ansible
from ansible.plugins.callback import CallbackBase
from ansible.plugins.callback.default import CallbackModule as DefaultCallbackModule

# AWX Display Callback
from .events import event_context
from .minimal import CallbackModule as MinimalCallbackModule

CENSORED = "the output has been hidden due to the fact that 'no_log: true' was specified for this result"  # noqa


class BaseCallbackModule(CallbackBase):
    '''
    Callback module for logging ansible/ansible-playbook events.
    '''

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'

    # These events should never have an associated play.
    EVENTS_WITHOUT_PLAY = [
        'playbook_on_start',
        'playbook_on_stats',
    ]

    # These events should never have an associated task.
    EVENTS_WITHOUT_TASK = EVENTS_WITHOUT_PLAY + [
        'playbook_on_setup',
        'playbook_on_notify',
        'playbook_on_import_for_host',
        'playbook_on_not_import_for_host',
        'playbook_on_no_hosts_matched',
        'playbook_on_no_hosts_remaining',
    ]

    def __init__(self):
        super(BaseCallbackModule, self).__init__()
        self.task_uuids = set()

    @contextlib.contextmanager
    def capture_event_data(self, event, **event_data):
        event_data.setdefault('uuid', str(uuid.uuid4()))

        if event not in self.EVENTS_WITHOUT_TASK:
            task = event_data.pop('task', None)
        else:
            task = None

        if event_data.get('res'):
            if event_data['res'].get('_ansible_no_log', False):
                event_data['res'] = {'censored': CENSORED}
            if event_data['res'].get('results', []):
                event_data['res']['results'] = copy(event_data['res']['results'])
            for i, item in enumerate(event_data['res'].get('results', [])):
                if isinstance(item, dict) and item.get('_ansible_no_log', False):
                    event_data['res']['results'][i] = {'censored': CENSORED}

        with event_context.display_lock:
            try:
                event_context.add_local(event=event, **event_data)
                if task:
                    self.set_task(task, local=True)
                event_context.dump_begin(sys.stdout)
                yield
            finally:
                event_context.dump_end(sys.stdout)
                if task:
                    self.clear_task(local=True)
                event_context.remove_local(event=None, **event_data)

    def set_playbook(self, playbook):
        # NOTE: Ansible doesn't generate a UUID for playbook_on_start so do it for them.
        self.playbook_uuid = str(uuid.uuid4())
        file_name = getattr(playbook, '_file_name', '???')
        event_context.add_global(playbook=file_name, playbook_uuid=self.playbook_uuid)
        self.clear_play()

    def set_play(self, play):
        if hasattr(play, 'hosts'):
            if isinstance(play.hosts, list):
                pattern = ','.join(play.hosts)
            else:
                pattern = play.hosts
        else:
            pattern = ''
        name = play.get_name().strip() or pattern
        event_context.add_global(play=name, play_uuid=str(play._uuid), play_pattern=pattern)
        self.clear_task()

    def clear_play(self):
        event_context.remove_global(play=None, play_uuid=None, play_pattern=None)
        self.clear_task()

    def set_task(self, task, local=False):
        # FIXME: Task is "global" unless using free strategy!
        task_ctx = dict(
            task=(task.name or task.action),
            task_uuid=str(task._uuid),
            task_action=task.action,
        )
        try:
            task_ctx['task_path'] = task.get_path()
        except AttributeError:
            pass
        if task.no_log:
            task_ctx['task_args'] = "the output has been hidden due to the fact that 'no_log: true' was specified for this result"
        else:
            task_args = ', '.join(('%s=%s' % a for a in task.args.items()))
            task_ctx['task_args'] = task_args
        if getattr(task, '_role', None):
            task_role = task._role._role_name
        else:
            task_role = getattr(task, 'role_name', '')
        if task_role:
            task_ctx['role'] = task_role
        if local:
            event_context.add_local(**task_ctx)
        else:
            event_context.add_global(**task_ctx)

    def clear_task(self, local=False):
        task_ctx = dict(task=None, task_path=None, task_uuid=None, task_action=None, task_args=None, role=None)
        if local:
            event_context.remove_local(**task_ctx)
        else:
            event_context.remove_global(**task_ctx)

    def v2_playbook_on_start(self, playbook):
        self.set_playbook(playbook)
        event_data = dict(
            uuid=self.playbook_uuid,
        )
        with self.capture_event_data('playbook_on_start', **event_data):
            super(BaseCallbackModule, self).v2_playbook_on_start(playbook)

    def v2_playbook_on_vars_prompt(self, varname, private=True, prompt=None,
                                   encrypt=None, confirm=False, salt_size=None,
                                   salt=None, default=None):
        event_data = dict(
            varname=varname,
            private=private,
            prompt=prompt,
            encrypt=encrypt,
            confirm=confirm,
            salt_size=salt_size,
            salt=salt,
            default=default,
        )
        with self.capture_event_data('playbook_on_vars_prompt', **event_data):
            super(BaseCallbackModule, self).v2_playbook_on_vars_prompt(
                varname, private, prompt, encrypt, confirm, salt_size, salt,
                default,
            )

    def v2_playbook_on_include(self, included_file):
        event_data = dict(
            included_file=included_file._filename if included_file is not None else None,
        )
        with self.capture_event_data('playbook_on_include', **event_data):
            super(BaseCallbackModule, self).v2_playbook_on_include(included_file)

    def v2_playbook_on_play_start(self, play):
        self.set_play(play)
        if hasattr(play, 'hosts'):
            if isinstance(play.hosts, list):
                pattern = ','.join(play.hosts)
            else:
                pattern = play.hosts
        else:
            pattern = ''
        name = play.get_name().strip() or pattern
        event_data = dict(
            name=name,
            pattern=pattern,
            uuid=str(play._uuid),
        )
        with self.capture_event_data('playbook_on_play_start', **event_data):
            super(BaseCallbackModule, self).v2_playbook_on_play_start(play)

    def v2_playbook_on_import_for_host(self, result, imported_file):
        # NOTE: Not used by Ansible 2.x.
        with self.capture_event_data('playbook_on_import_for_host'):
            super(BaseCallbackModule, self).v2_playbook_on_import_for_host(result, imported_file)

    def v2_playbook_on_not_import_for_host(self, result, missing_file):
        # NOTE: Not used by Ansible 2.x.
        with self.capture_event_data('playbook_on_not_import_for_host'):
            super(BaseCallbackModule, self).v2_playbook_on_not_import_for_host(result, missing_file)

    def v2_playbook_on_setup(self):
        # NOTE: Not used by Ansible 2.x.
        with self.capture_event_data('playbook_on_setup'):
            super(BaseCallbackModule, self).v2_playbook_on_setup()

    def v2_playbook_on_task_start(self, task, is_conditional):
        # FIXME: Flag task path output as vv.
        task_uuid = str(task._uuid)
        if task_uuid in self.task_uuids:
            # FIXME: When this task UUID repeats, it means the play is using the
            # free strategy, so different hosts may be running different tasks
            # within a play.
            return
        self.task_uuids.add(task_uuid)
        self.set_task(task)
        event_data = dict(
            task=task,
            name=task.get_name(),
            is_conditional=is_conditional,
            uuid=task_uuid,
        )
        with self.capture_event_data('playbook_on_task_start', **event_data):
            super(BaseCallbackModule, self).v2_playbook_on_task_start(task, is_conditional)

    def v2_playbook_on_cleanup_task_start(self, task):
        # NOTE: Not used by Ansible 2.x.
        self.set_task(task)
        event_data = dict(
            task=task,
            name=task.get_name(),
            uuid=str(task._uuid),
            is_conditional=True,
        )
        with self.capture_event_data('playbook_on_task_start', **event_data):
            super(BaseCallbackModule, self).v2_playbook_on_cleanup_task_start(task)

    def v2_playbook_on_handler_task_start(self, task):
        # NOTE: Re-using playbook_on_task_start event for this v2-specific
        # event, but setting is_conditional=True, which is how v1 identified a
        # task run as a handler.
        self.set_task(task)
        event_data = dict(
            task=task,
            name=task.get_name(),
            uuid=str(task._uuid),
            is_conditional=True,
        )
        with self.capture_event_data('playbook_on_task_start', **event_data):
            super(BaseCallbackModule, self).v2_playbook_on_handler_task_start(task)

    def v2_playbook_on_no_hosts_matched(self):
        with self.capture_event_data('playbook_on_no_hosts_matched'):
            super(BaseCallbackModule, self).v2_playbook_on_no_hosts_matched()

    def v2_playbook_on_no_hosts_remaining(self):
        with self.capture_event_data('playbook_on_no_hosts_remaining'):
            super(BaseCallbackModule, self).v2_playbook_on_no_hosts_remaining()

    def v2_playbook_on_notify(self, result, handler):
        # NOTE: Not used by Ansible 2.x.
        event_data = dict(
            host=result._host.get_name(),
            task=result._task,
            handler=handler,
        )
        with self.capture_event_data('playbook_on_notify', **event_data):
            super(BaseCallbackModule, self).v2_playbook_on_notify(result, handler)

    '''
    ansible_stats is, retoractively, added in 2.2
    '''
    def v2_playbook_on_stats(self, stats):
        self.clear_play()
        # FIXME: Add count of plays/tasks.
        event_data = dict(
            changed=stats.changed,
            dark=stats.dark,
            failures=stats.failures,
            ok=stats.ok,
            processed=stats.processed,
            skipped=stats.skipped,
            artifact_data=stats.custom.get('_run', {}) if hasattr(stats, 'custom') else {}
        )

        with self.capture_event_data('playbook_on_stats', **event_data):
            super(BaseCallbackModule, self).v2_playbook_on_stats(stats)

    def v2_runner_on_ok(self, result):
        # FIXME: Display detailed results or not based on verbosity.

        # strip environment vars from the job event; it already exists on the
        # job and sensitive values are filtered there
        if result._task.action in ('setup', 'gather_facts'):
            result._result.get('ansible_facts', {}).pop('ansible_env', None)

        event_data = dict(
            host=result._host.get_name(),
            remote_addr=result._host.address,
            task=result._task,
            res=result._result,
            event_loop=result._task.loop if hasattr(result._task, 'loop') else None,
        )
        with self.capture_event_data('runner_on_ok', **event_data):
            super(BaseCallbackModule, self).v2_runner_on_ok(result)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        # FIXME: Add verbosity for exception/results output.
        event_data = dict(
            host=result._host.get_name(),
            remote_addr=result._host.address,
            res=result._result,
            task=result._task,
            ignore_errors=ignore_errors,
            event_loop=result._task.loop if hasattr(result._task, 'loop') else None,
        )
        with self.capture_event_data('runner_on_failed', **event_data):
            super(BaseCallbackModule, self).v2_runner_on_failed(result, ignore_errors)

    def v2_runner_on_skipped(self, result):
        event_data = dict(
            host=result._host.get_name(),
            remote_addr=result._host.address,
            task=result._task,
            event_loop=result._task.loop if hasattr(result._task, 'loop') else None,
        )
        with self.capture_event_data('runner_on_skipped', **event_data):
            super(BaseCallbackModule, self).v2_runner_on_skipped(result)

    def v2_runner_on_unreachable(self, result):
        event_data = dict(
            host=result._host.get_name(),
            remote_addr=result._host.address,
            task=result._task,
            res=result._result,
        )
        with self.capture_event_data('runner_on_unreachable', **event_data):
            super(BaseCallbackModule, self).v2_runner_on_unreachable(result)

    def v2_runner_on_no_hosts(self, task):
        # NOTE: Not used by Ansible 2.x.
        event_data = dict(
            task=task,
        )
        with self.capture_event_data('runner_on_no_hosts', **event_data):
            super(BaseCallbackModule, self).v2_runner_on_no_hosts(task)

    def v2_runner_on_async_poll(self, result):
        # NOTE: Not used by Ansible 2.x.
        event_data = dict(
            host=result._host.get_name(),
            task=result._task,
            res=result._result,
            jid=result._result.get('ansible_job_id'),
        )
        with self.capture_event_data('runner_on_async_poll', **event_data):
            super(BaseCallbackModule, self).v2_runner_on_async_poll(result)

    def v2_runner_on_async_ok(self, result):
        # NOTE: Not used by Ansible 2.x.
        event_data = dict(
            host=result._host.get_name(),
            task=result._task,
            res=result._result,
            jid=result._result.get('ansible_job_id'),
        )
        with self.capture_event_data('runner_on_async_ok', **event_data):
            super(BaseCallbackModule, self).v2_runner_on_async_ok(result)

    def v2_runner_on_async_failed(self, result):
        # NOTE: Not used by Ansible 2.x.
        event_data = dict(
            host=result._host.get_name(),
            task=result._task,
            res=result._result,
            jid=result._result.get('ansible_job_id'),
        )
        with self.capture_event_data('runner_on_async_failed', **event_data):
            super(BaseCallbackModule, self).v2_runner_on_async_failed(result)

    def v2_runner_on_file_diff(self, result, diff):
        # NOTE: Not used by Ansible 2.x.
        event_data = dict(
            host=result._host.get_name(),
            task=result._task,
            diff=diff,
        )
        with self.capture_event_data('runner_on_file_diff', **event_data):
            super(BaseCallbackModule, self).v2_runner_on_file_diff(result, diff)

    def v2_on_file_diff(self, result):
        # NOTE: Logged as runner_on_file_diff.
        event_data = dict(
            host=result._host.get_name(),
            task=result._task,
            diff=result._result.get('diff'),
        )
        with self.capture_event_data('runner_on_file_diff', **event_data):
            super(BaseCallbackModule, self).v2_on_file_diff(result)

    def v2_runner_item_on_ok(self, result):
        event_data = dict(
            host=result._host.get_name(),
            task=result._task,
            res=result._result,
        )
        with self.capture_event_data('runner_item_on_ok', **event_data):
            super(BaseCallbackModule, self).v2_runner_item_on_ok(result)

    def v2_runner_item_on_failed(self, result):
        event_data = dict(
            host=result._host.get_name(),
            task=result._task,
            res=result._result,
        )
        with self.capture_event_data('runner_item_on_failed', **event_data):
            super(BaseCallbackModule, self).v2_runner_item_on_failed(result)

    def v2_runner_item_on_skipped(self, result):
        event_data = dict(
            host=result._host.get_name(),
            task=result._task,
            res=result._result,
        )
        with self.capture_event_data('runner_item_on_skipped', **event_data):
            super(BaseCallbackModule, self).v2_runner_item_on_skipped(result)

    def v2_runner_retry(self, result):
        event_data = dict(
            host=result._host.get_name(),
            task=result._task,
            res=result._result,
        )
        with self.capture_event_data('runner_retry', **event_data):
            super(BaseCallbackModule, self).v2_runner_retry(result)


class AWXDefaultCallbackModule(BaseCallbackModule, DefaultCallbackModule):

    CALLBACK_NAME = 'awx_display'


class AWXMinimalCallbackModule(BaseCallbackModule, MinimalCallbackModule):

    CALLBACK_NAME = 'minimal'

    def v2_playbook_on_play_start(self, play):
        pass

    def v2_playbook_on_task_start(self, task, is_conditional):
        self.set_task(task)

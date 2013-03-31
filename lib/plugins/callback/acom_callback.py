# (c) 2013, AnsibleWorks
#
# This file is part of Ansible Commander
#
# Ansible Commander is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible Commander is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible Commander.  If not, see <http://www.gnu.org/licenses/>.


import os
import sys

class CallbackModule(object):
    '''
    Callback module for logging ansible-playbook events to the database.
    '''

    def __init__(self):
        # he DJANGO_SETTINGS_MODULE environment variable *should* already
        # be set if this callback is called when executing a playbook via a
        # celery task, otherwise just bail out.
        settings_module_name = os.environ.get('DJANGO_SETTINGS_MODULE', None)
        if not settings_module_name:
            return
        # FIXME: Not particularly fond of this sys.path hack, but it is needed
        # when a celery task calls ansible-playbook and needs to execute this
        # script directly.
        try:
            settings_parent_module = __import__(settings_module_name)
        except ImportError:
            top_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..')
            sys.path.insert(0, os.path.abspath(top_dir))
            settings_parent_module = __import__(settings_module_name)
        settings_module = getattr(settings_parent_module, settings_module_name.split('.')[-1])
        # Use the ACOM_TEST_DATABASE_NAME environment variable to specify the test
        # database name when called from unit tests.
        if os.environ.get('ACOM_TEST_DATABASE_NAME', None):
            settings_module.DATABASES['default']['NAME'] = os.environ['ACOM_TEST_DATABASE_NAME']
        # Try to get the launch job status ID from the environment, otherwise
        # just bail out now.
        try:
            launch_job_status_pk = int(os.environ.get('ACOM_LAUNCH_JOB_STATUS_ID', ''))
        except ValueError:
            return
        from lib.main.models import LaunchJobStatus
        try:
            self.launch_job_status = LaunchJobStatus.objects.get(pk=launch_job_status_pk)
        except LaunchJobStatus.DoesNotExist:
            pass

    def _log_event(self, event, **event_data):
        #print '====', event, args, kwargs
        if hasattr(self, 'launch_job_status'):
            kwargs = {
                'event': event,
                'event_data': event_data,
            }
            self.launch_job_status.launch_job_status_events.create(**kwargs)

    def on_any(self, *args, **kwargs):
        pass

    def runner_on_failed(self, host, res, ignore_errors=False):
        self._log_event('runner_on_failed', host=host, res=res,
                        ignore_errors=ignore_errors)

    def runner_on_ok(self, host, res):
        self._log_event('runner_on_ok', host=host, res=res)

    def runner_on_error(self, host, msg):
        self._log_event('runner_on_error', host=host, msg=msg)

    def runner_on_skipped(self, host, item=None):
        self._log_event('runner_on_skipped', host=host, item=item)

    def runner_on_unreachable(self, host, res):
        self._log_event('runner_on_unreachable', host=host, res=res)

    def runner_on_no_hosts(self):
        self._log_event('runner_on_no_hosts')

    def runner_on_async_poll(self, host, res, jid, clock):
        self._log_event('runner_on_async_poll', host=host, res=res, jid=jid,
                        clock=clock)

    def runner_on_async_ok(self, host, res, jid):
        self._log_event('runner_on_async_ok', host=host, res=res, jid=jid)

    def runner_on_async_failed(self, host, res, jid):
        self._log_event('runner_on_async_failed', host=host, res=res, jid=jid)

    def playbook_on_start(self):
        self._log_event('playbook_on_start')

    def playbook_on_notify(self, host, handler):
        self._log_event('playbook_on_notify')

    def playbook_on_task_start(self, name, is_conditional):
        self._log_event('playbook_on_task_start', name=name,
                        is_conditional=is_conditional)

    def playbook_on_vars_prompt(self, varname, private=True, prompt=None,
                                encrypt=None, confirm=False, salt_size=None,
                                salt=None, default=None):
        self._log_event('playbook_on_vars_prompt', varname=varname,
                        private=private, prompt=prompt, encrypt=encrypt,
                        confirm=confirm, salt_size=salt_size, salt=salf,
                        default=default)

    def playbook_on_setup(self):
        self._log_event('playbook_on_setup')

    def playbook_on_import_for_host(self, host, imported_file):
        self._log_event('playbook_on_import_for_host', host=host,
                        imported_file=imported_file)

    def playbook_on_not_import_for_host(self, host, missing_file):
        self._log_event('playbook_on_not_import_for_host', host=host,
                        missing_file=missing_file)

    def playbook_on_play_start(self, pattern):
        self._log_event('playbook_on_play_start', pattern=pattern)

    def playbook_on_stats(self, stats):
        d = {}
        for attr in ('changed', 'dark', 'failures', 'ok', 'processed', 'skipped'):
            d[attr] = getattr(stats, attr)
        self._log_event('playbook_on_stats', **d)

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


class CallbackModule(object):
    '''
    Stub callback module for logging ansible-playbook events.
    '''

    def _log_event(self, event, *args, **kwargs):
        # FIXME: Push these events back to the server.
        pass#print '====', event, args, kwargs

    def on_any(self, *args, **kwargs):
        pass

    def runner_on_failed(self, host, res, ignore_errors=False):
        self._log_event('runner_on_failed', host, res, ignore_errors)

    def runner_on_ok(self, host, res):
        self._log_event('runner_on_ok', host, res)

    def runner_on_error(self, host, msg):
        self._log_event('runner_on_error', host, msg)

    def runner_on_skipped(self, host, item=None):
        self._log_event('runner_on_skipped', host, item)

    def runner_on_unreachable(self, host, res):
        self._log_event('runner_on_unreachable', host, res)

    def runner_on_no_hosts(self):
        self._log_event('runner_on_no_hosts')

    def runner_on_async_poll(self, host, res, jid, clock):
        self._log_event('runner_on_async_poll', host, res, jid, clock)

    def runner_on_async_ok(self, host, res, jid):
        self._log_event('runner_on_async_ok', host, res, jid)

    def runner_on_async_failed(self, host, res, jid):
        self._log_event('runner_on_async_failed', host, res, jid)

    def playbook_on_start(self):
        self._log_event('playbook_on_start')

    def playbook_on_notify(self, host, handler):
        self._log_event('playbook_on_notify')

    def playbook_on_task_start(self, name, is_conditional):
        self._log_event('playbook_on_task_start', name, is_conditional)

    def playbook_on_vars_prompt(self, varname, private=True, prompt=None, encrypt=None, confirm=False, salt_size=None, salt=None, default=None):
        self._log_event('playbook_on_vars_prompt', varname, private, prompt, encrypt, confirm, salt_size, salt, default)

    def playbook_on_setup(self):
        self._log_event('playbook_on_setup')

    def playbook_on_import_for_host(self, host, imported_file):
        self._log_event('playbook_on_import_for_host', host, imported_file)

    def playbook_on_not_import_for_host(self, host, missing_file):
        self._log_event('playbook_on_not_import_for_host', host, missing_file)

    def playbook_on_play_start(self, pattern):
        self._log_event('playbook_on_play_start', pattern)

    def playbook_on_stats(self, stats):
        d = {}
        for attr in ('changed', 'dark', 'failures', 'ok', 'processed', 'skipped'):
            d[attr] = getattr(stats, attr)
        self._log_event('playbook_on_stats', d)

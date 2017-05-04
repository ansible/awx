# (c) 2012-2014, Ansible, Inc
#
# This file is part of Ansible
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
__metaclass__ = type

from ansible.plugins.callback import CallbackBase
from websocket import create_connection
import json
from pprint import pprint

from functools import wraps

DEBUG = False


def debug(fn):
    if DEBUG:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            print('Calling', fn)
            ret_value = fn(*args, **kwargs)
            return ret_value
        return wrapper
    else:
        return fn
ass CallbackModule(CallbackBase):
    '''
    This callback puts results into a host specific file in a directory in json format.
    '''

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'ansible_upload'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self):
        super(CallbackModule, self).__init__()
        self.ws = create_connection("ws://127.0.0.1:8013/network_ui/ansible?topology_id=143")
        self.task = None
        self.play = None
        self.hosts = []

    @debug
    def v2_playbook_on_setup(self):
        pass

    @debug
    def v2_playbook_on_handler_task_start(self, task):
        pass

    @debug
    def v2_runner_on_ok(self, result):
        self.ws.send(json.dumps(['TaskStatus', dict(device_name=result._host.get_name(),
                                                    task_id=str(result._task._uuid),
                                                    working=False,
                                                    status="pass")]))

    @debug
    def v2_runner_on_failed(self, result, ignore_errors=False):
        self.ws.send(json.dumps(['TaskStatus', dict(device_name=result._host.get_name(),
                                                    task_id=str(result._task._uuid),
                                                    working=False,
                                                    status="fail")]))

    @debug
    def runner_on_unreachable(self, host, result, ignore_errors=False):
        self.ws.send(json.dumps(['TaskStatus', dict(device_name=host,
                                                    task_id=str(self.task._uuid),
                                                    working=False,
                                                    status="fail")]))

    @debug
    def v2_runner_item_on_skipped(self, result, ignore_errors=False):
        self.ws.send(json.dumps(['TaskStatus', dict(device_name=result._host.get_name(),
                                                    task_id=str(result._task._uuid),
                                                    working=False,
                                                    status="skip")]))

    @debug
    def DISABLED_v2_on_any(self, *args, **kwargs):
        self._display.display("--- play: {} task: {} ---".format(getattr(self.play, 'name', None), self.task))

        self._display.display("     --- ARGS ")
        for i, a in enumerate(args):
            self._display.display('     %s: %s' % (i, a))

        self._display.display("      --- KWARGS ")
        for k in kwargs:
            self._display.display('     %s: %s' % (k, kwargs[k]))
    @debug
    def v2_playbook_on_play_start(self, play):
        self.play = play
        self.hosts = play.get_variable_manager()._inventory.get_hosts()

        for host in self.hosts:
            self.ws.send(json.dumps(['DeviceStatus', dict(name=host.get_name(),
                                                          working=True,
                                                          status=None)]))

    @debug
    def v2_playbook_on_task_start(self, task, is_conditional):
        self.task = task
        for host in self.hosts:
            self.ws.send(json.dumps(['TaskStatus', dict(device_name=host.get_name(),
                                                        task_id=str(task._uuid),
                                                        working=True,
                                                        status=None)]))

    @debug
    def v2_playbook_on_stats(self, stats):
        hosts = sorted(stats.processed.keys())
   summary = {}
        for host in self.hosts:
            s = stats.summarize(host.get_name())
            status = "pass"
            status = "fail" if s['failures'] > 0 else status
            status = "fail" if s['unreachable'] > 0 else status
            self.ws.send(json.dumps(['DeviceStatus', dict(name=host.get_name(),
                                                          working=False,
                                                          status=status)]))

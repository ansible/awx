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
import base64
import contextlib
import datetime
import json
import multiprocessing
import os
import stat
import threading
import uuid

try:
    import memcache
except ImportError:
    raise ImportError('python-memcached is missing; {}bin/pip install python-memcached'.format(
        os.environ['VIRTUAL_ENV']
    ))

__all__ = ['event_context']


class IsolatedFileWrite:
    '''
    Stand-in class that will write partial event data to a file as a
    replacement for memcache when a job is running on an isolated host.
    '''

    def __init__(self):
        self.private_data_dir = os.getenv('AWX_ISOLATED_DATA_DIR')

    def set(self, key, value):
        # Strip off the leading memcache key identifying characters :1:ev-
        event_uuid = key[len(':1:ev-'):]
        # Write data in a staging area and then atomic move to pickup directory
        filename = '{}-partial.json'.format(event_uuid)
        dropoff_location = os.path.join(self.private_data_dir, 'artifacts', 'job_events', filename)
        write_location = '.'.join([dropoff_location, 'tmp'])
        with os.fdopen(os.open(write_location, os.O_WRONLY | os.O_CREAT, stat.S_IRUSR | stat.S_IWUSR), 'w') as f:
            f.write(value)
        os.rename(write_location, dropoff_location)


class EventContext(object):
    '''
    Store global and local (per thread/process) data associated with callback
    events and other display output methods.
    '''

    def __init__(self):
        self.display_lock = multiprocessing.RLock()
        cache_actual = os.getenv('CACHE', '127.0.0.1:11211')
        if os.getenv('AWX_ISOLATED_DATA_DIR', False):
            self.cache = IsolatedFileWrite()
        else:
            self.cache = memcache.Client([cache_actual], debug=0)

    def add_local(self, **kwargs):
        if not hasattr(self, '_local'):
            self._local = threading.local()
            self._local._ctx = {}
        self._local._ctx.update(kwargs)

    def remove_local(self, **kwargs):
        if hasattr(self, '_local'):
            for key in kwargs.keys():
                self._local._ctx.pop(key, None)

    @contextlib.contextmanager
    def set_local(self, **kwargs):
        try:
            self.add_local(**kwargs)
            yield
        finally:
            self.remove_local(**kwargs)

    def get_local(self):
        return getattr(getattr(self, '_local', None), '_ctx', {})

    def add_global(self, **kwargs):
        if not hasattr(self, '_global_ctx'):
            self._global_ctx = {}
        self._global_ctx.update(kwargs)

    def remove_global(self, **kwargs):
        if hasattr(self, '_global_ctx'):
            for key in kwargs.keys():
                self._global_ctx.pop(key, None)

    @contextlib.contextmanager
    def set_global(self, **kwargs):
        try:
            self.add_global(**kwargs)
            yield
        finally:
            self.remove_global(**kwargs)

    def get_global(self):
        return getattr(self, '_global_ctx', {})

    def get(self):
        ctx = {}
        ctx.update(self.get_global())
        ctx.update(self.get_local())
        return ctx

    def get_begin_dict(self):
        event_data = self.get()
        if os.getenv('JOB_ID', ''):
            event_data['job_id'] = int(os.getenv('JOB_ID', '0'))
        if os.getenv('AD_HOC_COMMAND_ID', ''):
            event_data['ad_hoc_command_id'] = int(os.getenv('AD_HOC_COMMAND_ID', '0'))
        if os.getenv('PROJECT_UPDATE_ID', ''):
            event_data['project_update_id'] = int(os.getenv('PROJECT_UPDATE_ID', '0'))
        event_data.setdefault('pid', os.getpid())
        event_data.setdefault('uuid', str(uuid.uuid4()))
        event_data.setdefault('created', datetime.datetime.utcnow().isoformat())
        if not event_data.get('parent_uuid', None) and event_data.get('job_id', None):
            for key in ('task_uuid', 'play_uuid', 'playbook_uuid'):
                parent_uuid = event_data.get(key, None)
                if parent_uuid and parent_uuid != event_data.get('uuid', None):
                    event_data['parent_uuid'] = parent_uuid
                    break

        event = event_data.pop('event', None)
        if not event:
            event = 'verbose'
            for key in ('debug', 'verbose', 'deprecated', 'warning', 'system_warning', 'error'):
                if event_data.get(key, False):
                    event = key
                    break
        max_res = int(os.getenv("MAX_EVENT_RES", 700000))
        if event not in ('playbook_on_stats',) and "res" in event_data and len(str(event_data['res'])) > max_res:
            event_data['res'] = {}
        event_dict = dict(event=event, event_data=event_data)
        for key in list(event_data.keys()):
            if key in ('job_id', 'ad_hoc_command_id', 'project_update_id', 'uuid', 'parent_uuid', 'created',):
                event_dict[key] = event_data.pop(key)
            elif key in ('verbosity', 'pid'):
                event_dict[key] = event_data[key]
        return event_dict

    def get_end_dict(self):
        return {}

    def dump(self, fileobj, data, max_width=78, flush=False):
        b64data = base64.b64encode(json.dumps(data).encode('utf-8')).decode()
        with self.display_lock:
            # pattern corresponding to OutputEventFilter expectation
            fileobj.write(u'\x1b[K')
            for offset in range(0, len(b64data), max_width):
                chunk = b64data[offset:offset + max_width]
                escaped_chunk = u'{}\x1b[{}D'.format(chunk, len(chunk))
                fileobj.write(escaped_chunk)
            fileobj.write(u'\x1b[K')
            if flush:
                fileobj.flush()

    def dump_begin(self, fileobj):
        begin_dict = self.get_begin_dict()
        self.cache.set(":1:ev-{}".format(begin_dict['uuid']), json.dumps(begin_dict))
        self.dump(fileobj, {'uuid': begin_dict['uuid']})

    def dump_end(self, fileobj):
        self.dump(fileobj, self.get_end_dict(), flush=True)


event_context = EventContext()

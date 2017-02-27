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
import functools
import sys
import uuid

# Ansible
from ansible.utils.display import Display

# Tower Display Callback
from .events import event_context

__all__ = []


def with_context(**context):
    global event_context

    def wrap(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            with event_context.set_local(**context):
                return f(*args, **kwargs)
        return wrapper
    return wrap


for attr in dir(Display):
    if attr.startswith('_') or 'cow' in attr or 'prompt' in attr:
        continue
    if attr in ('display', 'v', 'vv', 'vvv', 'vvvv', 'vvvvv', 'vvvvvv', 'verbose'):
        continue
    if not callable(getattr(Display, attr)):
        continue
    setattr(Display, attr, with_context(**{attr: True})(getattr(Display, attr)))


def with_verbosity(f):
    global event_context

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        host = args[2] if len(args) >= 3 else kwargs.get('host', None)
        caplevel = args[3] if len(args) >= 4 else kwargs.get('caplevel', 2)
        context = dict(verbose=True, verbosity=(caplevel + 1))
        if host is not None:
            context['remote_addr'] = host
        with event_context.set_local(**context):
            return f(*args, **kwargs)
    return wrapper


Display.verbose = with_verbosity(Display.verbose)


def display_with_context(f):

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        log_only = args[5] if len(args) >= 6 else kwargs.get('log_only', False)
        stderr = args[3] if len(args) >= 4 else kwargs.get('stderr', False)
        event_uuid = event_context.get().get('uuid', None)
        with event_context.display_lock:
            # If writing only to a log file or there is already an event UUID
            # set (from a callback module method), skip dumping the event data.
            if log_only or event_uuid:
                return f(*args, **kwargs)
            try:
                fileobj = sys.stderr if stderr else sys.stdout
                event_context.add_local(uuid=str(uuid.uuid4()))
                event_context.dump_begin(fileobj)
                return f(*args, **kwargs)
            finally:
                event_context.dump_end(fileobj)
                event_context.remove_local(uuid=None)

    return wrapper


Display.display = display_with_context(Display.display)

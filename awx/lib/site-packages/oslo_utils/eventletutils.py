# -*- coding: utf-8 -*-

#    Copyright (C) 2015 Yahoo! Inc. All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import warnings

from oslo_utils import importutils

# These may or may not exist; so carefully import them if we can...
_eventlet = importutils.try_import('eventlet')
_patcher = importutils.try_import('eventlet.patcher')

# Attribute that can be used by others to see if eventlet is even currently
# useable (can be used in unittests to skip test cases or test classes that
# require eventlet to work).
EVENTLET_AVAILABLE = all((_eventlet, _patcher))

# Taken from eventlet.py (v0.16.1) patcher code (it's not a accessible set
# for some reason...)
_ALL_PATCH = frozenset(['__builtin__', 'MySQLdb', 'os',
                        'psycopg', 'select', 'socket', 'thread', 'time'])


def warn_eventlet_not_patched(expected_patched_modules=None,
                              what='this library'):
    """Warns if eventlet is being used without patching provided modules.

    :param expected_patched_modules: list of modules to check to ensure that
                                     they are patched (and to warn if they
                                     are not); these names should correspond
                                     to the names passed into the eventlet
                                     monkey_patch() routine. If not provided
                                     then *all* the modules that could be
                                     patched are checked. The currently valid
                                     selection is one or multiple of
                                     ['MySQLdb', '__builtin__', 'all', 'os',
                                     'psycopg', 'select', 'socket', 'thread',
                                     'time'] (where 'all' has an inherent
                                     special meaning).
    :type expected_patched_modules: list/tuple/iterable
    :param what: string to merge into the warnings message to identify
                 what is being checked (used in forming the emitted warnings
                 message).
    :type what: string
    """
    if not expected_patched_modules:
        expanded_patched_modules = _ALL_PATCH.copy()
    else:
        expanded_patched_modules = set()
        for m in expected_patched_modules:
            if m == 'all':
                expanded_patched_modules.update(_ALL_PATCH)
            else:
                if m not in _ALL_PATCH:
                    raise ValueError("Unknown module '%s' requested to check"
                                     " if patched" % m)
                else:
                    expanded_patched_modules.add(m)
    if EVENTLET_AVAILABLE:
        try:
            # The patcher code stores a dictionary here of all modules
            # names -> whether it was patched...
            #
            # Example:
            #
            # >>> _patcher.monkey_patch(os=True)
            # >>> print(_patcher.already_patched)
            # {'os': True}
            maybe_patched = bool(_patcher.already_patched)
        except AttributeError:
            # Assume it is patched (the attribute used here doesn't appear
            # to be a public documented API so we will assume that everything
            # is patched when that attribute isn't there to be safe...)
            maybe_patched = True
        if maybe_patched:
            not_patched = []
            for m in sorted(expanded_patched_modules):
                if not _patcher.is_monkey_patched(m):
                    not_patched.append(m)
            if not_patched:
                warnings.warn("It is highly recommended that when eventlet"
                              " is used that the %s modules are monkey"
                              " patched when using %s (to avoid"
                              " spurious or unexpected lock-ups"
                              " and/or hangs)" % (not_patched, what),
                              RuntimeWarning, stacklevel=3)

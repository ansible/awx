# Copyright (c) 2015 Ansible, Inc.
# This file is a utility Ansible plugin that is not part of the AWX or Ansible
# packages.  It does not import any code from either package, nor does its
# license apply to Ansible or AWX.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
#    Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
#    Neither the name of the <ORGANIZATION> nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import sys
import time
import datetime
from copy import deepcopy
from ansible import constants as C
from ansible.cache.base import BaseCacheModule

try:
    import zmq
except ImportError:
    print("pyzmq is required")
    sys.exit(1)

class CacheModule(BaseCacheModule):

    def __init__(self, *args, **kwargs):

        # Basic in-memory caching for typical runs
        self._cache = {}
        self._cache_prev = {}

        # This is the local tower zmq connection
        self._tower_connection = C.CACHE_PLUGIN_CONNECTION
        self.date_key = time.mktime(datetime.datetime.utcnow().timetuple())
        try:
            self.context = zmq.Context()
            self.socket = self.context.socket(zmq.REQ)
            self.socket.setsockopt(zmq.RCVTIMEO, 4000)
            self.socket.setsockopt(zmq.LINGER, 2000)
            self.socket.connect(self._tower_connection)
        except Exception, e:
            print("Connection to zeromq failed at %s with error: %s" % (str(self._tower_connection),
                                                                        str(e)))
            sys.exit(1)

    def filter_ansible_facts(self, facts):
        return dict((k, facts[k]) for k in facts.keys() if k.startswith('ansible_'))

    def identify_new_module(self, key, value):
        # Return the first key found that doesn't exist in the
        # previous set of facts
        if key in self._cache_prev:
            value_old = self._cache_prev[key]
            for k,v in value.iteritems():
                if k not in value_old:
                    if not k.startswith('ansible_'):
                        return k
        # First time we have seen facts from this host
        # it's either ansible facts or a module facts (including module_setup)
        elif len(value) == 1:
            return value.iterkeys().next()
        return None

    def get(self, key):
        return self._cache.get(key)

    '''
    get() returns a reference to the fact object (usually a dict). The object is modified directly,
    then set is called. Effectively, pre-determining the set logic.

    The below logic creates a backup of the cache each set. The values are now preserved across set() calls.

    For a given key. The previous value is looked at for new keys that aren't of the form 'ansible_'.
    If found, send the value of the found key.
    If not found, send all the key value pairs of the form 'ansible_' (we presume set() is called because
    of an ansible fact module invocation)

    More simply stated...
    In value, if a new key is found at the top most dict then consider this a module request and only 
    emit the facts for the found top-level key.

    If a new key is not found, assume set() was called as a result of ansible facts scan. Thus, emit 
    all facts of the form 'ansible_'.
    '''
    def set(self, key, value):
        module = self.identify_new_module(key, value)
        # Assume ansible fact triggered the set if no new module found
        facts = self.filter_ansible_facts(value) if not module else dict({ module : value[module]})

        self._cache_prev = deepcopy(self._cache)
        self._cache[key] = value

        # Emit fact data to tower for processing
        self.socket.send_json(dict(host=key, facts=facts, date_key=self.date_key))
        self.socket.recv()

    def keys(self):
        return self._cache.keys()

    def contains(self, key):
        return key in self._cache

    def delete(self, key):
        del self._cache[key]

    def flush(self):
        self._cache = {}

    def copy(self):
        return self._cache.copy()

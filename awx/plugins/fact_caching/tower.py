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

import os
import time

try:
    from ansible.cache.base import BaseCacheModule
except:
    from ansible.plugins.cache.base import BaseCacheModule

from kombu import Connection, Exchange, Producer


class CacheModule(BaseCacheModule):

    def __init__(self, *args, **kwargs):
        # Basic in-memory caching for typical runs
        self._cache = {}
        self._all_keys = {}

        self.date_key = time.time()
        self.callback_connection = os.environ['CALLBACK_CONNECTION']
        self.callback_queue = os.environ['FACT_QUEUE']
        self.connection = Connection(self.callback_connection)
        self.exchange = Exchange(self.callback_queue, type='direct')
        self.producer = Producer(self.connection)

    def filter_ansible_facts(self, facts):
        return dict((k, facts[k]) for k in facts.keys() if k.startswith('ansible_'))

    def identify_new_module(self, key, value):
        # Return the first key found that doesn't exist in the
        # previous set of facts
        if key in self._all_keys:
            for k in value.iterkeys():
                if k not in self._all_keys[key] and not k.startswith('ansible_'):
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
        self._cache[key] = value
        self._all_keys[key] = value.keys()
        packet = {
            'host': key,
            'inventory_id': os.environ['INVENTORY_ID'],
            'facts': facts,
            'date_key': self.date_key,
        }

        # Emit fact data to tower for processing
        self.producer.publish(packet,
                              serializer='json',
                              compression='bzip2',
                              exchange=self.exchange,
                              declare=[self.exchange],
                              routing_key=self.callback_queue)

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

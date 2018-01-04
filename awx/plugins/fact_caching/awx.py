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
import memcache
import json
import datetime
import base64
from dateutil import parser
from dateutil.tz import tzutc

from ansible import constants as C

try:
    from ansible.cache.base import BaseCacheModule
except Exception:
    from ansible.plugins.cache.base import BaseCacheModule


class CacheModule(BaseCacheModule):

    def __init__(self, *args, **kwargs):
        self.mc = memcache.Client([C.CACHE_PLUGIN_CONNECTION], debug=0)
        self._timeout = int(C.CACHE_PLUGIN_TIMEOUT)
        self._inventory_id = os.environ['INVENTORY_ID']

    @property
    def host_names_key(self):
        return '{}'.format(self._inventory_id)

    def translate_host_key(self, host_name):
        return '{}-{}'.format(self._inventory_id, base64.b64encode(host_name.encode('utf-8')))

    def translate_modified_key(self, host_name):
        return '{}-{}-modified'.format(self._inventory_id, base64.b64encode(host_name.encode('utf-8')))

    def get(self, key):
        host_key = self.translate_host_key(key)
        modified_key = self.translate_modified_key(key)

        '''
        Cache entry expired
        '''
        modified = self.mc.get(modified_key)
        if modified is None:
            raise KeyError
        modified = parser.parse(modified).replace(tzinfo=tzutc())
        now_utc = datetime.datetime.now(tzutc())
        if self._timeout != 0 and (modified + datetime.timedelta(seconds=self._timeout)) < now_utc:
            raise KeyError

        value_json = self.mc.get(host_key)
        if value_json is None:
            raise KeyError
        try:
            return json.loads(value_json)
        # If cache entry is corrupt or bad, fail gracefully.
        except (TypeError, ValueError):
            self.delete(key)
            raise KeyError

    def set(self, key, value):
        host_key = self.translate_host_key(key)
        modified_key = self.translate_modified_key(key)

        self.mc.set(host_key, json.dumps(value))
        value = json.dumps(value)
        rc = self.mc.set(host_key, value)
        if rc == 0 and len(value) > self.mc.server_max_value_length:
            self._display.error(
                "memcache.set('{}', '?') failed, value > server_max_value_length ({} bytes)".format(
                    key, len(value)
                )
            )
        self.mc.set(modified_key, datetime.datetime.now(tzutc()).isoformat())

    def keys(self):
        return self.mc.get(self.host_names_key)

    def contains(self, key):
        try:
            self.get(key)
            return True
        except KeyError:
            return False

    def delete(self, key):
        self.set(key, {})

    def flush(self):
        host_names = self.mc.get(self.host_names_key)
        if not host_names:
            return

        for k in host_names:
            self.mc.delete(self.translate_host_key(k))
            self.mc.delete(self.translate_modified_key(k))

    def copy(self):
        ret = dict()
        host_names = self.mc.get(self.host_names_key)
        if not host_names:
            return

        for k in host_names:
            ret[k] = self.mc.get(self.translate_host_key(k))
        return ret


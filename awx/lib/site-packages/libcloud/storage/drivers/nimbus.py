# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time
import hashlib
import hmac

try:
    import simplejson as json
except ImportError:
    import json  # NOQA

from libcloud.utils.py3 import httplib
from libcloud.utils.py3 import urlencode

from libcloud.common.base import ConnectionUserAndKey, JsonResponse
from libcloud.common.types import InvalidCredsError, LibcloudError
from libcloud.storage.base import Container, StorageDriver


class NimbusResponse(JsonResponse):
    valid_response_codes = [httplib.OK, httplib.NOT_FOUND, httplib.CONFLICT,
                            httplib.BAD_REQUEST]

    def success(self):
        return self.status in self.valid_response_codes

    def parse_error(self):
        if self.status in [httplib.UNAUTHORIZED]:
            raise InvalidCredsError(self.body)
        raise LibcloudError('Unknown error. Status code: %d' % (self.status),
                            driver=self.driver)


class NimbusConnection(ConnectionUserAndKey):
    host = 'nimbus.io'
    responseCls = NimbusResponse

    def __init__(self, *args, **kwargs):
        self.id = kwargs.pop('id')
        super(NimbusConnection, self).__init__(*args, **kwargs)

    def pre_connect_hook(self, params, headers):
        timestamp = str(int(time.time()))
        signature = self._calculate_signature(user_id=self.user_id,
                                              method=self.method,
                                              params=params,
                                              path=self.action,
                                              timestamp=timestamp,
                                              key=self.key)
        headers['X-NIMBUS-IO-Timestamp'] = timestamp
        headers['Authorization'] = 'NIMBUS.IO %s:%s' % (self.id, signature)
        return params, headers

    def _calculate_signature(self, user_id, method, params, path, timestamp,
                             key):
        if params:
            uri_path = path + '?' + urlencode(params)
        else:
            uri_path = path

        string_to_sign = [user_id, method, str(timestamp), uri_path]
        string_to_sign = '\n'.join(string_to_sign)

        hmac_value = hmac.new(key, string_to_sign, hashlib.sha256)
        return hmac_value.hexdigest()


class NimbusStorageDriver(StorageDriver):
    name = 'Nimbus.io'
    website = 'https://nimbus.io/'
    connectionCls = NimbusConnection

    def __init__(self, *args, **kwargs):
        self.user_id = kwargs['user_id']
        super(NimbusStorageDriver, self).__init__(*args, **kwargs)

    def iterate_containers(self):
        response = self.connection.request('/customers/%s/collections' %
                                           (self.connection.user_id))
        return self._to_containers(response.object)

    def create_container(self, container_name):
        params = {'action': 'create', 'name': container_name}
        response = self.connection.request('/customers/%s/collections' %
                                           (self.connection.user_id),
                                           params=params,
                                           method='POST')
        return self._to_container(response.object)

    def _to_containers(self, data):
        for item in data:
            yield self._to_container(item)

    def _to_container(self, data):
        name = data[0]
        extra = {'date_created': data[2]}
        return Container(name=name, extra=extra, driver=self)

    def _ex_connection_class_kwargs(self):
        result = {'id': self.user_id}
        return result

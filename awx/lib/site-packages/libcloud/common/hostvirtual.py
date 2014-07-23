# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

try:
    import simplejson as json
except ImportError:
    import json

from libcloud.utils.py3 import httplib
from libcloud.common.base import ConnectionKey, JsonResponse
from libcloud.compute.types import InvalidCredsError
from libcloud.common.types import LibcloudError

API_HOST = 'vapi.vr.org'


class HostVirtualException(LibcloudError):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        self.args = (code, message)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return '<HostVirtualException in %d: %s>' % (self.code, self.message)


class HostVirtualConnection(ConnectionKey):
    host = API_HOST

    allow_insecure = False

    def add_default_params(self, params):
        params['key'] = self.key
        return params


class HostVirtualResponse(JsonResponse):
    valid_response_codes = [httplib.OK, httplib.ACCEPTED, httplib.CREATED,
                            httplib.NO_CONTENT]

    def parse_body(self):
        if not self.body:
            return None

        data = json.loads(self.body)
        return data

    def parse_error(self):
        data = self.parse_body()

        if self.status == httplib.UNAUTHORIZED:
            raise InvalidCredsError('%(code)s:%(message)s' % (data['error']))
        elif self.status == httplib.PRECONDITION_FAILED:
            raise HostVirtualException(
                data['error']['code'], data['error']['message'])
        elif self.status == httplib.NOT_FOUND:
            raise HostVirtualException(
                data['error']['code'], data['error']['message'])

        return self.body

    def success(self):
        return self.status in self.valid_response_codes

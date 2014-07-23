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

import base64

from libcloud.common.base import ConnectionUserAndKey, JsonResponse
from libcloud.compute.types import InvalidCredsError

from libcloud.utils.py3 import b
from libcloud.utils.py3 import httplib

try:
    import simplejson as json
except ImportError:
    import json


class BrightboxResponse(JsonResponse):
    def success(self):
        return self.status >= httplib.OK and self.status < httplib.BAD_REQUEST

    def parse_body(self):
        if self.headers['content-type'].split(';')[0] == 'application/json':
            return super(BrightboxResponse, self).parse_body()
        else:
            return self.body

    def parse_error(self):
        response = super(BrightboxResponse, self).parse_body()

        if 'error' in response:
            if response['error'] in ['invalid_client', 'unauthorized_client']:
                raise InvalidCredsError(response['error'])

            return response['error']
        elif 'error_name' in response:
            return '%s: %s' % (response['error_name'], response['errors'][0])

        return self.body


class BrightboxConnection(ConnectionUserAndKey):
    """
    Connection class for the Brightbox driver
    """

    host = 'api.gb1.brightbox.com'
    responseCls = BrightboxResponse

    def _fetch_oauth_token(self):
        body = json.dumps({'client_id': self.user_id, 'grant_type': 'none'})

        authorization = 'Basic ' + str(base64.encodestring(b('%s:%s' %
                                       (self.user_id, self.key)))).rstrip()

        self.connect()

        headers = {
            'Host': self.host,
            'User-Agent': self._user_agent(),
            'Authorization': authorization,
            'Content-Type': 'application/json',
            'Content-Length': str(len(body))
        }

        response = self.connection.request(method='POST', url='/token',
                                           body=body, headers=headers)

        response = self.connection.getresponse()

        if response.status == httplib.OK:
            return json.loads(response.read())['access_token']
        else:
            responseCls = BrightboxResponse(response=response, connection=self)
            message = responseCls.parse_error()
            raise InvalidCredsError(message)

    def add_default_headers(self, headers):
        try:
            headers['Authorization'] = 'OAuth ' + self.token
        except AttributeError:
            self.token = self._fetch_oauth_token()

            headers['Authorization'] = 'OAuth ' + self.token

        return headers

    def encode_data(self, data):
        return json.dumps(data)

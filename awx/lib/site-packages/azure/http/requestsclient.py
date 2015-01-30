#-------------------------------------------------------------------------
# Copyright (c) Microsoft.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#--------------------------------------------------------------------------

class _Response(object):

    ''' Response class corresponding to the response returned from httplib
    HTTPConnection. '''

    def __init__(self, response):
        self.status = response.status_code
        self.reason = response.reason
        self.respbody = response.content
        self.length = len(response.content)
        self.headers = []
        for key, name in response.headers.items():
            self.headers.append((key.lower(), name))

    def getheaders(self):
        '''Returns response headers.'''
        return self.headers

    def read(self, _length):
        '''Returns response body. '''
        return self.respbody[:_length]


class _RequestsConnection(object):

    def __init__(self, host, protocol, session):
        self.host = host
        self.protocol = protocol
        self.session = session
        self.headers = {}
        self.method = None
        self.body = None
        self.response = None
        self.uri = None

    def close(self):
        pass

    def set_tunnel(self, host, port=None, headers=None):
        pass

    def set_proxy_credentials(self, user, password):
        pass

    def putrequest(self, method, uri):
        self.method = method
        self.uri = self.protocol + '://' + self.host + uri

    def putheader(self, name, value):
        self.headers[name] = value

    def endheaders(self):
        pass

    def send(self, request_body):
        self.response = self.session.request(self.method, self.uri, data=request_body, headers=self.headers)

    def getresponse(self):
        return _Response(self.response)

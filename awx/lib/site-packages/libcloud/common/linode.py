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

from libcloud.common.base import ConnectionKey, JsonResponse
from libcloud.common.types import InvalidCredsError

from libcloud.utils.py3 import PY3
from libcloud.utils.py3 import b

__all__ = [
    'API_HOST',
    'API_ROOT',
    'LinodeException',
    'LinodeResponse',
    'LinodeConnection'
]

# Endpoint for the Linode API
API_HOST = 'api.linode.com'
API_ROOT = '/'

# Constants that map a RAM figure to a PlanID (updated 4/25/14)
LINODE_PLAN_IDS = {2048: '1',
                   4096: '3',
                   8192: '5',
                   16384: '6',
                   32768: '7',
                   49152: '8',
                   65536: '9',
                   98304: '11'}


class LinodeException(Exception):
    """Error originating from the Linode API

    This class wraps a Linode API error, a list of which is available in the
    API documentation.  All Linode API errors are a numeric code and a
    human-readable description.
    """
    def __init__(self, code, message):
        self.code = code
        self.message = message
        self.args = (code, message)

    def __str__(self):
        return "(%u) %s" % (self.code, self.message)

    def __repr__(self):
        return "<LinodeException code %u '%s'>" % (self.code, self.message)


class LinodeResponse(JsonResponse):
    """Linode API response

    Wraps the HTTP response returned by the Linode API, which should be JSON in
    this structure:

       {
         "ERRORARRAY": [ ... ],
         "DATA": [ ... ],
         "ACTION": " ... "
       }

    libcloud does not take advantage of batching, so a response will always
    reflect the above format.  A few weird quirks are caught here as well."""
    def __init__(self, response, connection):
        """Instantiate a LinodeResponse from the HTTP response

        :keyword response: The raw response returned by urllib
        :return: parsed :class:`LinodeResponse`"""

        self.connection = connection

        self.headers = dict(response.getheaders())
        self.error = response.reason
        self.status = response.status

        self.body = self._decompress_response(body=response.read(),
                                              headers=self.headers)

        if PY3:
            self.body = b(self.body).decode('utf-8')

        self.invalid = LinodeException(0xFF,
                                       "Invalid JSON received from server")

        # Move parse_body() to here;  we can't be sure of failure until we've
        # parsed the body into JSON.
        self.objects, self.errors = self.parse_body()

        if not self.success():
            # Raise the first error, as there will usually only be one
            raise self.errors[0]

    def parse_body(self):
        """Parse the body of the response into JSON objects

        If the response chokes the parser, action and data will be returned as
        None and errorarray will indicate an invalid JSON exception.

        :return: ``list`` of objects and ``list`` of errors"""
        js = super(LinodeResponse, self).parse_body()

        try:
            if isinstance(js, dict):
                # solitary response - promote to list
                js = [js]
            ret = []
            errs = []
            for obj in js:
                if ("DATA" not in obj or "ERRORARRAY" not in obj
                        or "ACTION" not in obj):
                    ret.append(None)
                    errs.append(self.invalid)
                    continue
                ret.append(obj["DATA"])
                errs.extend(self._make_excp(e) for e in obj["ERRORARRAY"])
            return (ret, errs)
        except:
            return (None, [self.invalid])

    def success(self):
        """Check the response for success

        The way we determine success is by the presence of an error in
        ERRORARRAY.  If one is there, we assume the whole request failed.

        :return: ``bool`` indicating a successful request"""
        return len(self.errors) == 0

    def _make_excp(self, error):
        """Convert an API error to a LinodeException instance

        :keyword error: JSON object containing ``ERRORCODE`` and
        ``ERRORMESSAGE``
        :type error: dict"""
        if "ERRORCODE" not in error or "ERRORMESSAGE" not in error:
            return None
        if error["ERRORCODE"] == 4:
            return InvalidCredsError(error["ERRORMESSAGE"])
        return LinodeException(error["ERRORCODE"], error["ERRORMESSAGE"])


class LinodeConnection(ConnectionKey):
    """
    A connection to the Linode API

    Wraps SSL connections to the Linode API, automagically injecting the
    parameters that the API needs for each request.
    """
    host = API_HOST
    responseCls = LinodeResponse

    def add_default_params(self, params):
        """
        Add parameters that are necessary for every request

        This method adds ``api_key`` and ``api_responseFormat`` to
        the request.
        """
        params["api_key"] = self.key
        # Be explicit about this in case the default changes.
        params["api_responseFormat"] = "json"
        return params

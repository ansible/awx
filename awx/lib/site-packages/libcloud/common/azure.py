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

import copy
import time
import base64
import hmac

from hashlib import sha256

from libcloud.utils.py3 import httplib
from libcloud.utils.py3 import b
from libcloud.utils.xml import fixxpath

try:
    from lxml import etree as ET
except ImportError:
    from xml.etree import ElementTree as ET

from libcloud.common.types import InvalidCredsError
from libcloud.common.types import LibcloudError, MalformedResponseError
from libcloud.common.base import ConnectionUserAndKey, RawResponse
from libcloud.common.base import XmlResponse

# Azure API version
API_VERSION = '2012-02-12'

# The time format for headers in Azure requests
AZURE_TIME_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'


class AzureResponse(XmlResponse):

    valid_response_codes = [httplib.NOT_FOUND, httplib.CONFLICT,
                            httplib.BAD_REQUEST]

    def success(self):
        i = int(self.status)
        return i >= 200 and i <= 299 or i in self.valid_response_codes

    def parse_error(self, msg=None):
        error_msg = 'Unknown error'

        try:
            # Azure does give some meaningful errors, but is inconsistent
            # Some APIs respond with an XML error. Others just dump HTML
            body = self.parse_body()

            if type(body) == ET.Element:
                code = body.findtext(fixxpath(xpath='Code'))
                message = body.findtext(fixxpath(xpath='Message'))
                message = message.split('\n')[0]
                error_msg = '%s: %s' % (code, message)

        except MalformedResponseError:
            pass

        if msg:
            error_msg = '%s - %s' % (msg, error_msg)

        if self.status in [httplib.UNAUTHORIZED, httplib.FORBIDDEN]:
            raise InvalidCredsError(error_msg)

        raise LibcloudError('%s Status code: %d.' % (error_msg, self.status),
                            driver=self)


class AzureRawResponse(RawResponse):
    pass


class AzureConnection(ConnectionUserAndKey):
    """
    Represents a single connection to Azure
    """

    responseCls = AzureResponse
    rawResponseCls = AzureRawResponse

    def add_default_params(self, params):
        return params

    def pre_connect_hook(self, params, headers):
        headers = copy.deepcopy(headers)

        # We have to add a date header in GMT
        headers['x-ms-date'] = time.strftime(AZURE_TIME_FORMAT, time.gmtime())
        headers['x-ms-version'] = API_VERSION

        # Add the authorization header
        headers['Authorization'] = self._get_azure_auth_signature(
            method=self.method, headers=headers, params=params,
            account=self.user_id, secret_key=self.key, path=self.action)

        # Azure cribs about this in 'raw' connections
        headers.pop('Host', None)

        return params, headers

    def _get_azure_auth_signature(self, method, headers, params,
                                  account, secret_key, path='/'):
        """
        Signature = Base64( HMAC-SHA1( YourSecretAccessKeyID,
                            UTF-8-Encoding-Of( StringToSign ) ) ) );

        StringToSign = HTTP-VERB + "\n" +
            Content-Encoding + "\n" +
            Content-Language + "\n" +
            Content-Length + "\n" +
            Content-MD5 + "\n" +
            Content-Type + "\n" +
            Date + "\n" +
            If-Modified-Since + "\n" +
            If-Match + "\n" +
            If-None-Match + "\n" +
            If-Unmodified-Since + "\n" +
            Range + "\n" +
            CanonicalizedHeaders +
            CanonicalizedResource;
        """
        special_header_values = []
        xms_header_values = []
        param_list = []
        special_header_keys = ['content-encoding', 'content-language',
                               'content-length', 'content-md5',
                               'content-type', 'date', 'if-modified-since',
                               'if-match', 'if-none-match',
                               'if-unmodified-since', 'range']

        # Split the x-ms headers and normal headers and make everything
        # lower case
        headers_copy = {}
        for header, value in headers.items():
            header = header.lower()
            value = str(value).strip()
            if header.startswith('x-ms-'):
                xms_header_values.append((header, value))
            else:
                headers_copy[header] = value

        # Get the values for the headers in the specific order
        for header in special_header_keys:
            header = header.lower()  # Just for safety
            if header in headers_copy:
                special_header_values.append(headers_copy[header])
            else:
                special_header_values.append('')

        # Prepare the first section of the string to be signed
        values_to_sign = [method] + special_header_values
        # string_to_sign = '\n'.join([method] + special_header_values)

        # The x-ms-* headers have to be in lower case and sorted
        xms_header_values.sort()

        for header, value in xms_header_values:
            values_to_sign.append('%s:%s' % (header, value))

        # Add the canonicalized path
        values_to_sign.append('/%s%s' % (account, path))

        # URL query parameters (sorted and lower case)
        for key, value in params.items():
            param_list.append((key.lower(), str(value).strip()))

        param_list.sort()

        for key, value in param_list:
            values_to_sign.append('%s:%s' % (key, value))

        string_to_sign = b('\n'.join(values_to_sign))
        secret_key = b(secret_key)
        b64_hmac = base64.b64encode(
            hmac.new(secret_key, string_to_sign, digestmod=sha256).digest()
        )

        return 'SharedKey %s:%s' % (self.user_id, b64_hmac.decode('utf-8'))

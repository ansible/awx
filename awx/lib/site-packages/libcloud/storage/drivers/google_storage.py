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
import copy
import hmac

from email.utils import formatdate
from hashlib import sha1

from libcloud.utils.py3 import b

from libcloud.common.base import ConnectionUserAndKey

from libcloud.storage.drivers.s3 import BaseS3StorageDriver, S3Response
from libcloud.storage.drivers.s3 import S3RawResponse

SIGNATURE_IDENTIFIER = 'GOOG1'

# Docs are a lie. Actual namespace returned is different that the one listed in
# the docs.
AUTH_HOST = 'commondatastorage.googleapis.com'
API_VERSION = '2006-03-01'
NAMESPACE = 'http://doc.s3.amazonaws.com/%s' % (API_VERSION)


class GoogleStorageConnection(ConnectionUserAndKey):
    """
    Repersents a single connection to the Google storage API endpoint.
    """

    host = AUTH_HOST
    responseCls = S3Response
    rawResponseCls = S3RawResponse

    def add_default_headers(self, headers):
        date = formatdate(usegmt=True)
        headers['Date'] = date
        return headers

    def pre_connect_hook(self, params, headers):
        signature = self._get_aws_auth_param(method=self.method,
                                             headers=headers,
                                             params=params,
                                             expires=None,
                                             secret_key=self.key,
                                             path=self.action)
        headers['Authorization'] = '%s %s:%s' % (SIGNATURE_IDENTIFIER,
                                                 self.user_id, signature)
        return params, headers

    def _get_aws_auth_param(self, method, headers, params, expires,
                            secret_key, path='/'):
        # TODO: Refactor and re-use in S3 driver
        """
        Signature = URL-Encode( Base64( HMAC-SHA1( YourSecretAccessKeyID,
                                UTF-8-Encoding-Of( StringToSign ) ) ) );

        StringToSign = HTTP-VERB + "\n" +
            Content-MD5 + "\n" +
            Content-Type + "\n" +
            Date + "\n" +
            CanonicalizedHeaders +
            CanonicalizedResource;
        """
        special_header_keys = ['content-md5', 'content-type', 'date']
        special_header_values = {}
        extension_header_values = {}

        headers_copy = copy.deepcopy(headers)
        for key, value in list(headers_copy.items()):
            if key.lower() in special_header_keys:
                if key.lower() == 'date':
                    value = value.strip()
                else:
                    value = value.lower().strip()
                special_header_values[key.lower()] = value
            elif key.lower().startswith('x-goog-'):
                extension_header_values[key.lower()] = value.strip()

        if 'content-md5' not in special_header_values:
            special_header_values['content-md5'] = ''

        if 'content-type' not in special_header_values:
            special_header_values['content-type'] = ''

        keys_sorted = list(special_header_values.keys())
        keys_sorted.sort()

        buf = [method]
        for key in keys_sorted:
            value = special_header_values[key]
            buf.append(value)
        string_to_sign = '\n'.join(buf)

        keys_sorted = list(extension_header_values.keys())
        keys_sorted.sort()

        extension_header_string = []
        for key in keys_sorted:
            value = extension_header_values[key]
            extension_header_string.append('%s:%s' % (key, value))
        extension_header_string = '\n'.join(extension_header_string)

        values_to_sign = []
        for value in [string_to_sign, extension_header_string, path]:
            if value:
                values_to_sign.append(value)

        string_to_sign = '\n'.join(values_to_sign)
        b64_hmac = base64.b64encode(
            hmac.new(b(secret_key), b(string_to_sign), digestmod=sha1).digest()
        )
        return b64_hmac.decode('utf-8')


class GoogleStorageDriver(BaseS3StorageDriver):
    name = 'Google Storage'
    website = 'http://cloud.google.com/'
    connectionCls = GoogleStorageConnection
    hash_type = 'md5'
    namespace = NAMESPACE
    supports_chunked_encoding = False
    supports_s3_multipart_upload = False

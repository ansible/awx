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

from libcloud.utils.py3 import urlparse, parse_qs
from libcloud.common.base import Connection

__all__ = [
    'get_response_object'
]


def get_response_object(url):
    """
    Utility function which uses libcloud's connection class to issue an HTTP
    request.

    :param url: URL to send the request to.
    :type url: ``str``

    :return: Response object.
    :rtype: :class:`Response`.
    """
    parsed_url = urlparse.urlparse(url)
    parsed_qs = parse_qs(parsed_url.query)
    secure = parsed_url.scheme == 'https'

    con = Connection(secure=secure, host=parsed_url.netloc)
    response = con.request(method='GET', action=parsed_url.path,
                           params=parsed_qs)
    return response

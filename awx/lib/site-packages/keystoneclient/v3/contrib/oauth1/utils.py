# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import six
from six.moves.urllib import parse as urlparse


OAUTH_PATH = '/OS-OAUTH1'


def get_oauth_token_from_body(body):
    """Parse the URL response body to retrieve the oauth token key and secret

    The response body will look like:
    'oauth_token=12345&oauth_token_secret=67890' with
    'oauth_expires_at=2013-03-30T05:27:19.463201' possibly there, too.
    """

    if six.PY3:
        body = body.decode('utf-8')

    credentials = urlparse.parse_qs(body)
    key = credentials['oauth_token'][0]
    secret = credentials['oauth_token_secret'][0]
    token = {'key': key, 'id': key, 'secret': secret}
    expires_at = credentials.get('oauth_expires_at')
    if expires_at:
        token['expires'] = expires_at[0]
    return token

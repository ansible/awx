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

from __future__ import unicode_literals

from keystoneclient import auth
from keystoneclient import base
from keystoneclient.v3.contrib.oauth1 import utils

try:
    from oauthlib import oauth1
except ImportError:
    oauth1 = None


class AccessToken(base.Resource):
    pass


class AccessTokenManager(base.CrudManager):
    """Manager class for manipulating identity OAuth access tokens."""
    resource_class = AccessToken

    def create(self, consumer_key, consumer_secret, request_key,
               request_secret, verifier):
        endpoint = utils.OAUTH_PATH + '/access_token'
        oauth_client = oauth1.Client(consumer_key,
                                     client_secret=consumer_secret,
                                     resource_owner_key=request_key,
                                     resource_owner_secret=request_secret,
                                     signature_method=oauth1.SIGNATURE_HMAC,
                                     verifier=verifier)
        url = self.api.get_endpoint(interface=auth.AUTH_INTERFACE).rstrip('/')
        url, headers, body = oauth_client.sign(url + endpoint,
                                               http_method='POST')
        resp, body = self.client.post(endpoint, headers=headers)
        token = utils.get_oauth_token_from_body(resp.content)
        return self.resource_class(self, token)

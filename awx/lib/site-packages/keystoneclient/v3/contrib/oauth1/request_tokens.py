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

from six.moves.urllib import parse as urlparse

from keystoneclient import auth
from keystoneclient import base
from keystoneclient.v3.contrib.oauth1 import utils

try:
    from oauthlib import oauth1
except ImportError:
    oauth1 = None


class RequestToken(base.Resource):
    def authorize(self, roles):
        try:
            retval = self.manager.authorize(self.id, roles)
            self = retval
        except Exception:
            retval = None

        return retval


class RequestTokenManager(base.CrudManager):
    """Manager class for manipulating identity OAuth request tokens."""
    resource_class = RequestToken

    def authorize(self, request_token, roles):
        """Authorize a request token with specific roles.

        Utilize Identity API operation:
        PUT /OS-OAUTH1/authorize/$request_token_id

        :param request_token: a request token that will be authorized, and
            can be exchanged for an access token.
        :param roles: a list of roles, that will be delegated to the user.
        """

        request_id = urlparse.quote(base.getid(request_token))
        endpoint = utils.OAUTH_PATH + '/authorize/%s' % (request_id)
        body = {'roles': [{'id': base.getid(r_id)} for r_id in roles]}
        return self._put(endpoint, body, "token")

    def create(self, consumer_key, consumer_secret, project):
        endpoint = utils.OAUTH_PATH + '/request_token'
        headers = {'requested-project-id': base.getid(project)}
        oauth_client = oauth1.Client(consumer_key,
                                     client_secret=consumer_secret,
                                     signature_method=oauth1.SIGNATURE_HMAC,
                                     callback_uri="oob")
        url = self.api.get_endpoint(interface=auth.AUTH_INTERFACE).rstrip("/")
        url, headers, body = oauth_client.sign(url + endpoint,
                                               http_method='POST',
                                               headers=headers)
        resp, body = self.client.post(endpoint, headers=headers)
        token = utils.get_oauth_token_from_body(resp.content)
        return self.resource_class(self, token)

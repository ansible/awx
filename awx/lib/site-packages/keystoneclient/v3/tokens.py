# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from keystoneclient import access
from keystoneclient import base
from keystoneclient import utils


def _calc_id(token):
    if isinstance(token, access.AccessInfo):
        return token.auth_token

    return base.getid(token)


class TokenManager(object):
    """Manager class for manipulating Identity tokens."""

    def __init__(self, client):
        self._client = client

    def revoke_token(self, token):
        """Revoke a token.

        :param token: Token to be revoked. This can be an instance of
                      :py:class:`keystoneclient.access.AccessInfo` or a string
                      token_id.
        """

        token_id = _calc_id(token)
        headers = {'X-Subject-Token': token_id}
        return self._client.delete('/auth/tokens', headers=headers)

    def get_revoked(self):
        """Get revoked tokens list.

        :returns: A dict containing "signed" which is a CMS formatted string.
        :rtype: dict

        """

        resp, body = self._client.get('/auth/tokens/OS-PKI/revoked')
        return body

    @utils.positional.method(1)
    def validate(self, token, include_catalog=True):
        """Validate a token.

        :param token: Token to be validated. This can be an instance of
                      :py:class:`keystoneclient.access.AccessInfo` or a string
                      token_id.
        :param include_catalog: If False, the response is requested to not
                                include the catalog.

        :rtype: :py:class:`keystoneclient.access.AccessInfoV3`

        """

        token_id = _calc_id(token)
        headers = {'X-Subject-Token': token_id}

        url = '/auth/tokens'
        if not include_catalog:
            url += '?nocatalog'

        resp, body = self._client.get(url, headers=headers)

        access_info = access.AccessInfo.factory(resp=resp, body=body)
        return access_info

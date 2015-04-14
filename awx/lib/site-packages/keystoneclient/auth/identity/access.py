# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from keystoneclient.auth.identity import base
from keystoneclient import utils


class AccessInfoPlugin(base.BaseIdentityPlugin):
    """A plugin that turns an existing AccessInfo object into a usable plugin.

    There are cases where reuse of an auth_ref or AccessInfo object is
    warranted such as from a cache, from auth_token middleware, or another
    source.

    Turn the existing access info object into an identity plugin. This plugin
    cannot be refreshed as the AccessInfo object does not contain any
    authorizing information.

    :param auth_ref: the existing AccessInfo object.
    :type auth_ref: keystoneclient.access.AccessInfo
    :param auth_url: the url where this AccessInfo was retrieved from. Required
                     if using the AUTH_INTERFACE with get_endpoint. (optional)
    """

    @utils.positional()
    def __init__(self, auth_ref, auth_url=None):
        super(AccessInfoPlugin, self).__init__(auth_url=auth_url,
                                               reauthenticate=False)
        self.auth_ref = auth_ref

    def get_auth_ref(self, session, **kwargs):
        return self.auth_ref

    def invalidate(self):
        # NOTE(jamielennox): Don't allow the default invalidation to occur
        # because on next authentication request we will only get the same
        # auth_ref object again.
        return False

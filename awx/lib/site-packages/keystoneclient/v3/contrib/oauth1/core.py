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

from keystoneclient.i18n import _
from keystoneclient.v3.contrib.oauth1 import access_tokens
from keystoneclient.v3.contrib.oauth1 import consumers
from keystoneclient.v3.contrib.oauth1 import request_tokens


def create_oauth_manager(self):
    # NOTE(stevemar): Attempt to import the oauthlib package at this point.
    try:
        import oauthlib  # noqa
    # NOTE(stevemar): Return an object instead of raising an exception here,
    # this will allow users to see an exception only when trying to access the
    # oauth portions of client. Otherwise an exception would be raised
    # when the client is created.
    except ImportError:
        return OAuthManagerOptionalImportProxy()
    else:
        return OAuthManager(self)


class OAuthManager(object):
    def __init__(self, api):
        self.access_tokens = access_tokens.AccessTokenManager(api)
        self.consumers = consumers.ConsumerManager(api)
        self.request_tokens = request_tokens.RequestTokenManager(api)


class OAuthManagerOptionalImportProxy(object):
    """Act as a proxy manager in case oauthlib is no installed.

    This class will only be created if oauthlib is not in the system,
    trying to access any of the attributes in name (access_tokens,
    consumers, request_tokens), will result in a NotImplementedError,
    and a message.

    >>> manager.access_tokens.blah
    NotImplementedError: To use 'access_tokens' oauthlib must be installed

    Otherwise, if trying to access an attribute other than the ones in name,
    the manager will state that the attribute does not exist.

    >>> manager.dne.blah
    AttributeError: 'OAuthManagerOptionalImportProxy' object has no
    attribute 'dne'
    """

    def __getattribute__(self, name):
        if name in ('access_tokens', 'consumers', 'request_tokens'):
            raise NotImplementedError(
                _('To use %r oauthlib must be installed') % name)
        return super(OAuthManagerOptionalImportProxy,
                     self).__getattribute__(name)

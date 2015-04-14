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

import logging

from oslo_config import cfg

from keystoneclient import _discover
from keystoneclient.auth.identity.generic import base
from keystoneclient.auth.identity import v2
from keystoneclient.auth.identity import v3

LOG = logging.getLogger(__name__)


def get_options():
    return [
        cfg.StrOpt('token', help='Token to authenticate with'),
    ]


class Token(base.BaseGenericPlugin):
    """Generic token auth plugin.

    :param string token: Token for authentication.
    """

    def __init__(self, auth_url, token=None, **kwargs):
        super(Token, self).__init__(auth_url, **kwargs)
        self._token = token

    def create_plugin(self, session, version, url, raw_status=None):
        if _discover.version_match((2,), version):
            return v2.Token(url, self._token, **self._v2_params)

        elif _discover.version_match((3,), version):
            return v3.Token(url, self._token, **self._v3_params)

    @classmethod
    def get_options(cls):
        options = super(Token, cls).get_options()
        options.extend(get_options())
        return options

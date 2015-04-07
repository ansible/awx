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

from oslo_config import cfg

from keystoneclient.auth import base


class Token(base.BaseAuthPlugin):
    """A provider that will always use the given token and endpoint.

    This is really only useful for testing and in certain CLI cases where you
    have a known endpoint and admin token that you want to use.
    """

    def __init__(self, endpoint, token):
        # NOTE(jamielennox): endpoint is reserved for when plugins
        # can be used to provide that information
        self.endpoint = endpoint
        self.token = token

    def get_token(self, session):
        return self.token

    def get_endpoint(self, session, **kwargs):
        """Return the supplied endpoint.

        Using this plugin the same endpoint is returned regardless of the
        parameters passed to the plugin.
        """
        return self.endpoint

    @classmethod
    def get_options(cls):
        options = super(Token, cls).get_options()

        options.extend([
            cfg.StrOpt('endpoint',
                       help='The endpoint that will always be used'),
            cfg.StrOpt('token',
                       secret=True,
                       help='The token that will always be used'),
        ])

        return options

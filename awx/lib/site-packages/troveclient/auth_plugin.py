# Copyright 2014 Rackspace
# Copyright 2013 OpenStack Foundation
# Copyright 2013 Spanish National Research Council.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import logging

import pkg_resources
import six

from troveclient import exceptions
from troveclient.openstack.common.gettextutils import _  # noqa


logger = logging.getLogger(__name__)


_discovered_plugins = {}


def discover_auth_systems():
    """Discover the available auth-systems.

    This won't take into account the old style auth-systems.
    """
    ep_name = 'openstack.client.auth_plugin'
    for ep in pkg_resources.iter_entry_points(ep_name):
        try:
            auth_plugin = ep.load()
        except (ImportError, pkg_resources.UnknownExtra, AttributeError) as e:
            logger.debug(_("ERROR: Cannot load auth plugin %s") % ep.name)
            logger.debug(e, exc_info=1)
        else:
            _discovered_plugins[ep.name] = auth_plugin


def load_auth_system_opts(parser):
    """Load options needed by the available auth-systems into a parser.

    This function will try to populate the parser with options from the
    available plugins.
    """
    for name, auth_plugin in six.iteritems(_discovered_plugins):
        add_opts_fn = getattr(auth_plugin, "add_opts", None)
        if add_opts_fn:
            group = parser.add_argument_group("Auth-system '%s' options" %
                                              name)
            add_opts_fn(group)


def load_plugin(auth_system):
    if auth_system in _discovered_plugins:
        return _discovered_plugins[auth_system]()

    raise exceptions.AuthSystemNotFound(auth_system)


class BaseAuthPlugin(object):
    """Base class for authentication plugins.

    An authentication plugin needs to override at least the authenticate
    method to be a valid plugin.
    """
    def __init__(self):
        self.opts = {}

    def get_auth_url(self):
        """Return the auth url for the plugin (if any)."""
        return None

    @staticmethod
    def add_opts(parser):
        """Populate and return the parser with the options for this plugin.

        If the plugin does not need any options, it should return the same
        parser untouched.
        """
        return parser

    def parse_opts(self, args):
        """Parse the actual auth-system options if any.

        This method is expected to populate the attribute self.opts with a
        dict containing the options and values needed to make authentication.
        If the dict is empty, the client should assume that it needs the same
        options as the 'keystone' auth system (i.e. os_username and
        os_password).

        Returns the self.opts dict.
        """
        return self.opts

    def authenticate(self, cls, auth_url):
        """Authenticate using plugin defined method."""
        raise exceptions.AuthSystemNotFound(self.auth_system)

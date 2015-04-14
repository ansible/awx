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

import abc
import logging

from oslo_config import cfg
import six
import six.moves.urllib.parse as urlparse

from keystoneclient import _discover
from keystoneclient.auth.identity import base
from keystoneclient import exceptions
from keystoneclient.i18n import _, _LW


LOG = logging.getLogger(__name__)


def get_options():
    return [
        cfg.StrOpt('domain-id', help='Domain ID to scope to'),
        cfg.StrOpt('domain-name', help='Domain name to scope to'),
        cfg.StrOpt('tenant-id', help='Tenant ID to scope to'),
        cfg.StrOpt('tenant-name', help='Tenant name to scope to'),
        cfg.StrOpt('project-id', help='Project ID to scope to'),
        cfg.StrOpt('project-name', help='Project name to scope to'),
        cfg.StrOpt('project-domain-id',
                   help='Domain ID containing project'),
        cfg.StrOpt('project-domain-name',
                   help='Domain name containing project'),
        cfg.StrOpt('trust-id', help='Trust ID'),
    ]


@six.add_metaclass(abc.ABCMeta)
class BaseGenericPlugin(base.BaseIdentityPlugin):
    """An identity plugin that is not version dependant.

    Internally we will construct a version dependant plugin with the resolved
    URL and then proxy all calls from the base plugin to the versioned one.
    """

    def __init__(self, auth_url,
                 tenant_id=None,
                 tenant_name=None,
                 project_id=None,
                 project_name=None,
                 project_domain_id=None,
                 project_domain_name=None,
                 domain_id=None,
                 domain_name=None,
                 trust_id=None):
        super(BaseGenericPlugin, self).__init__(auth_url=auth_url)

        self._project_id = project_id or tenant_id
        self._project_name = project_name or tenant_name
        self._project_domain_id = project_domain_id
        self._project_domain_name = project_domain_name
        self._domain_id = domain_id
        self._domain_name = domain_name
        self._trust_id = trust_id

        self._plugin = None

    @abc.abstractmethod
    def create_plugin(self, session, version, url, raw_status=None):
        """Create a plugin from the given paramters.

        This function will be called multiple times with the version and url
        of a potential endpoint. If a plugin can be constructed that fits the
        params then it should return it. If not return None and then another
        call will be made with other available URLs.

        :param session: A session object.
        :type session: keystoneclient.session.Session
        :param tuple version: A tuple of the API version at the URL.
        :param string url: The base URL for this version.
        :param string raw_status: The status that was in the discovery field.

        :returns: A plugin that can match the parameters or None if nothing.
        """
        return None

    @property
    def _has_domain_scope(self):
        """Are there domain parameters.

        Domain parameters are v3 only so returns if any are set.

        :returns: True if a domain parameter is set, false otherwise.
        """
        return any([self._domain_id, self._domain_name,
                    self._project_domain_id, self._project_domain_name])

    @property
    def _v2_params(self):
        """Parameters that are common to v2 plugins."""
        return {'trust_id': self._trust_id,
                'tenant_id': self._project_id,
                'tenant_name': self._project_name}

    @property
    def _v3_params(self):
        """Parameters that are common to v3 plugins."""
        return {'trust_id': self._trust_id,
                'project_id': self._project_id,
                'project_name': self._project_name,
                'project_domain_id': self._project_domain_id,
                'project_domain_name': self._project_domain_name,
                'domain_id': self._domain_id,
                'domain_name': self._domain_name}

    def _do_create_plugin(self, session):
        plugin = None

        try:
            disc = self.get_discovery(session,
                                      self.auth_url,
                                      authenticated=False)
        except (exceptions.DiscoveryFailure,
                exceptions.HTTPError,
                exceptions.ConnectionError):
            LOG.warn(_LW('Discovering versions from the identity service '
                         'failed when creating the password plugin. '
                         'Attempting to determine version from URL.'))

            url_parts = urlparse.urlparse(self.auth_url)
            path = url_parts.path.lower()

            if path.startswith('/v2.0') and not self._has_domain_scope:
                plugin = self.create_plugin(session, (2, 0), self.auth_url)
            elif path.startswith('/v3'):
                plugin = self.create_plugin(session, (3, 0), self.auth_url)

        else:
            disc_data = disc.version_data()

            for data in disc_data:
                version = data['version']

                if (_discover.version_match((2,), version) and
                        self._has_domain_scope):
                    # NOTE(jamielennox): if there are domain parameters there
                    # is no point even trying against v2 APIs.
                    continue

                plugin = self.create_plugin(session,
                                            version,
                                            data['url'],
                                            raw_status=data['raw_status'])

                if plugin:
                    break

        if plugin:
            return plugin

        # so there were no URLs that i could use for auth of any version.
        msg = _('Could not determine a suitable URL for the plugin')
        raise exceptions.DiscoveryFailure(msg)

    def get_auth_ref(self, session, **kwargs):
        if not self._plugin:
            self._plugin = self._do_create_plugin(session)

        return self._plugin.get_auth_ref(session, **kwargs)

    @classmethod
    def get_options(cls):
        options = super(BaseGenericPlugin, cls).get_options()
        options.extend(get_options())
        return options

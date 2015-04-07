# Copyright 2010 OpenStack Foundation
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

from six.moves.urllib import parse as urlparse

from keystoneclient import exceptions
from keystoneclient import httpclient
from keystoneclient.i18n import _, _LE


_logger = logging.getLogger(__name__)


class Client(httpclient.HTTPClient):
    """Client for the OpenStack Keystone pre-version calls API.

    :param string endpoint: A user-supplied endpoint URL for the keystone
                            service.
    :param integer timeout: Allows customization of the timeout for client
                            http requests. (optional)

    Example::

        >>> from keystoneclient.generic import client
        >>> root = client.Client(auth_url=KEYSTONE_URL)
        >>> versions = root.discover()
        ...
        >>> from keystoneclient.v2_0 import client as v2client
        >>> keystone = v2client.Client(auth_url=versions['v2.0']['url'])
        ...
        >>> user = keystone.users.get(USER_ID)
        >>> user.delete()

    """

    def __init__(self, endpoint=None, **kwargs):
        """Initialize a new client for the Keystone v2.0 API."""
        super(Client, self).__init__(endpoint=endpoint, **kwargs)
        self.endpoint = endpoint

    def discover(self, url=None):
        """Discover Keystone servers and return API versions supported.

        :param url: optional url to test (without version)

        Returns::

            {
                'message': 'Keystone found at http://127.0.0.1:5000/',
                'v2.0': {
                    'status': 'beta',
                    'url': 'http://127.0.0.1:5000/v2.0/',
                    'id': 'v2.0'
                },
            }

        """
        if url:
            return self._check_keystone_versions(url)
        else:
            return self._local_keystone_exists()

    def _local_keystone_exists(self):
        """Checks if Keystone is available on default local port 35357."""
        results = self._check_keystone_versions("http://localhost:35357")
        if results is None:
            results = self._check_keystone_versions("https://localhost:35357")
        return results

    def _check_keystone_versions(self, url):
        """Calls Keystone URL and detects the available API versions."""
        try:
            resp, body = self.request(url, "GET",
                                      headers={'Accept':
                                               'application/json'})
            # Multiple Choices status code is returned by the root
            # identity endpoint, with references to one or more
            # Identity API versions -- v3 spec
            # some cases we get No Content
            if resp.status_code in (200, 204, 300):
                try:
                    results = {}
                    if 'version' in body:
                        results['message'] = _("Keystone found at %s") % url
                        version = body['version']
                        # Stable/diablo incorrect format
                        id, status, version_url = (
                            self._get_version_info(version, url))
                        results[str(id)] = {"id": id,
                                            "status": status,
                                            "url": version_url}
                        return results
                    elif 'versions' in body:
                        # Correct format
                        results['message'] = _("Keystone found at %s") % url
                        for version in body['versions']['values']:
                            id, status, version_url = (
                                self._get_version_info(version, url))
                            results[str(id)] = {"id": id,
                                                "status": status,
                                                "url": version_url}
                        return results
                    else:
                        results['message'] = (
                            _("Unrecognized response from %s") % url)
                    return results
                except KeyError:
                    raise exceptions.AuthorizationFailure()
            elif resp.status_code == 305:
                return self._check_keystone_versions(resp['location'])
            else:
                raise exceptions.from_response(resp, "GET", url)
        except Exception:
            _logger.exception(_LE('Failed to detect available versions.'))

    def discover_extensions(self, url=None):
        """Discover Keystone extensions supported.

        :param url: optional url to test (should have a version in it)

        Returns::

            {
                'message': 'Keystone extensions at http://127.0.0.1:35357/v2',
                'OS-KSEC2': 'OpenStack EC2 Credentials Extension',
            }

        """
        if url:
            return self._check_keystone_extensions(url)

    def _check_keystone_extensions(self, url):
        """Calls Keystone URL and detects the available extensions."""
        try:
            if not url.endswith("/"):
                url += '/'
            resp, body = self.request("%sextensions" % url, "GET",
                                      headers={'Accept':
                                               'application/json'})
            if resp.status_code in (200, 204):  # some cases we get No Content
                if 'extensions' in body and 'values' in body['extensions']:
                    # Parse correct format (per contract)
                    extensions = body['extensions']['values']
                elif 'extensions' in body:
                    # Support incorrect, but prevalent format
                    extensions = body['extensions']
                else:
                    return dict(message=(
                        _('Unrecognized extensions response from %s') % url))

                return dict(self._get_extension_info(e) for e in extensions)
            elif resp.status_code == 305:
                return self._check_keystone_extensions(resp['location'])
            else:
                raise exceptions.from_response(
                    resp, "GET", "%sextensions" % url)
        except Exception:
            _logger.exception(_LE('Failed to check keystone extensions.'))

    @staticmethod
    def _get_version_info(version, root_url):
        """Parses version information.

        :param version: a dict of a Keystone version response
        :param root_url: string url used to construct
            the version if no URL is provided.
        :returns: tuple - (verionId, versionStatus, versionUrl)
        """
        id = version['id']
        status = version['status']
        ref = urlparse.urljoin(root_url, id)
        if 'links' in version:
            for link in version['links']:
                if link['rel'] == 'self':
                    ref = link['href']
                    break
        return (id, status, ref)

    @staticmethod
    def _get_extension_info(extension):
        """Parses extension information.

        :param extension: a dict of a Keystone extension response
        :returns: tuple - (alias, name)
        """
        alias = extension['alias']
        name = extension['name']
        return (alias, name)

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

"""The passive components to version discovery.

The Discover object in discover.py contains functions that can create objects
on your behalf. These functions are not usable from within the keystoneclient
library because you will get dependency resolution issues.

The Discover object in this file provides the querying components of Discovery.
This includes functions like url_for which allow you to retrieve URLs and the
raw data specified in version discovery responses.
"""

import logging
import re

from keystoneclient import exceptions
from keystoneclient.i18n import _, _LI, _LW
from keystoneclient import utils


_LOGGER = logging.getLogger(__name__)


@utils.positional()
def get_version_data(session, url, authenticated=None):
    """Retrieve raw version data from a url."""
    headers = {'Accept': 'application/json'}

    resp = session.get(url, headers=headers, authenticated=authenticated)

    try:
        body_resp = resp.json()
    except ValueError:
        pass
    else:
        # In the event of querying a root URL we will get back a list of
        # available versions.
        try:
            return body_resp['versions']['values']
        except (KeyError, TypeError):
            pass

        # Most servers don't have a 'values' element so accept a simple
        # versions dict if available.
        try:
            return body_resp['versions']
        except KeyError:
            pass

        # Otherwise if we query an endpoint like /v2.0 then we will get back
        # just the one available version.
        try:
            return [body_resp['version']]
        except KeyError:
            pass

    err_text = resp.text[:50] + '...' if len(resp.text) > 50 else resp.text
    msg = _('Invalid Response - Bad version data returned: %s') % err_text
    raise exceptions.DiscoveryFailure(msg)


def normalize_version_number(version):
    """Turn a version representation into a tuple."""

    # trim the v from a 'v2.0' or similar
    try:
        version = version.lstrip('v')
    except AttributeError:
        pass

    # if it's an integer or a numeric as a string then normalize it
    # to a string, this ensures 1 decimal point
    try:
        num = float(version)
    except Exception:
        pass
    else:
        version = str(num)

    # if it's a string (or an integer) from above break it on .
    try:
        return tuple(map(int, version.split('.')))
    except Exception:
        pass

    # last attempt, maybe it's a list or iterable.
    try:
        return tuple(map(int, version))
    except Exception:
        pass

    raise TypeError(_('Invalid version specified: %s') % version)


def version_match(required, candidate):
    """Test that an available version is a suitable match for a required
    version.

    To be suitable a version must be of the same major version as required
    and be at least a match in minor/patch level.

    eg. 3.3 is a match for a required 3.1 but 4.1 is not.

    :param tuple required: the version that must be met.
    :param tuple candidate: the version to test against required.

    :returns: True if candidate is suitable False otherwise.
    :rtype: bool
    """
    # major versions must be the same (e.g. even though v2 is a lower
    # version than v3 we can't use it if v2 was requested)
    if candidate[0] != required[0]:
        return False

    # prevent selecting a minor version less than what is required
    if candidate < required:
        return False

    return True


class Discover(object):

    CURRENT_STATUSES = ('stable', 'current', 'supported')
    DEPRECATED_STATUSES = ('deprecated',)
    EXPERIMENTAL_STATUSES = ('experimental',)

    @utils.positional()
    def __init__(self, session, url, authenticated=None):
        self._data = get_version_data(session, url,
                                      authenticated=authenticated)

    def raw_version_data(self, allow_experimental=False,
                         allow_deprecated=True, allow_unknown=False):
        """Get raw version information from URL.

        Raw data indicates that only minimal validation processing is performed
        on the data, so what is returned here will be the data in the same
        format it was received from the endpoint.

        :param bool allow_experimental: Allow experimental version endpoints.
        :param bool allow_deprecated: Allow deprecated version endpoints.
        :param bool allow_unknown: Allow endpoints with an unrecognised status.

        :returns: The endpoints returned from the server that match the
                  criteria.
        :rtype: list
        """
        versions = []
        for v in self._data:
            try:
                status = v['status']
            except KeyError:
                _LOGGER.warning(_LW('Skipping over invalid version data. '
                                    'No stability status in version.'))
                continue

            status = status.lower()

            if status in self.CURRENT_STATUSES:
                versions.append(v)
            elif status in self.DEPRECATED_STATUSES:
                if allow_deprecated:
                    versions.append(v)
            elif status in self.EXPERIMENTAL_STATUSES:
                if allow_experimental:
                    versions.append(v)
            elif allow_unknown:
                versions.append(v)

        return versions

    def version_data(self, **kwargs):
        """Get normalized version data.

        Return version data in a structured way.

        :returns: A list of version data dictionaries sorted by version number.
                  Each data element in the returned list is a dictionary
                  consisting of at least:

          :version tuple: The normalized version of the endpoint.
          :url str: The url for the endpoint.
          :raw_status str: The status as provided by the server
        :rtype: list(dict)
        """
        data = self.raw_version_data(**kwargs)
        versions = []

        for v in data:
            try:
                version_str = v['id']
            except KeyError:
                _LOGGER.info(_LI('Skipping invalid version data. Missing ID.'))
                continue

            try:
                links = v['links']
            except KeyError:
                _LOGGER.info(
                    _LI('Skipping invalid version data. Missing links'))
                continue

            version_number = normalize_version_number(version_str)

            for link in links:
                try:
                    rel = link['rel']
                    url = link['href']
                except (KeyError, TypeError):
                    _LOGGER.info(_LI('Skipping invalid version link. '
                                     'Missing link URL or relationship.'))
                    continue

                if rel.lower() == 'self':
                    break
            else:
                _LOGGER.info(_LI('Skipping invalid version data. '
                                 'Missing link to endpoint.'))
                continue

            versions.append({'version': version_number,
                             'url': url,
                             'raw_status': v['status']})

        versions.sort(key=lambda v: v['version'])
        return versions

    def data_for(self, version, **kwargs):
        """Return endpoint data for a version.

        :param tuple version: The version is always a minimum version in the
            same major release as there should be no compatibility issues with
            using a version newer than the one asked for.

        :returns: the endpoint data for a URL that matches the required version
                  (the format is described in version_data) or None if no
                  match.
        :rtype: dict
        """
        version = normalize_version_number(version)
        version_data = self.version_data(**kwargs)

        for data in reversed(version_data):
            if version_match(version, data['version']):
                return data

        return None

    def url_for(self, version, **kwargs):
        """Get the endpoint url for a version.

        :param tuple version: The version is always a minimum version in the
            same major release as there should be no compatibility issues with
            using a version newer than the one asked for.

        :returns: The url for the specified version or None if no match.
        :rtype: str
        """
        data = self.data_for(version, **kwargs)
        return data['url'] if data else None


class _VersionHacks(object):
    """A container to abstract the list of version hacks.

    This could be done as simply a dictionary but is abstracted like this to
    make for easier testing.
    """

    def __init__(self):
        self._discovery_data = {}

    def add_discover_hack(self, service_type, old, new=''):
        """Add a new hack for a service type.

        :param str service_type: The service_type in the catalog.
        :param re.RegexObject old: The pattern to use.
        :param str new: What to replace the pattern with.
        """
        hacks = self._discovery_data.setdefault(service_type, [])
        hacks.append((old, new))

    def get_discover_hack(self, service_type, url):
        """Apply the catalog hacks and figure out an unversioned endpoint.

        :param str service_type: the service_type to look up.
        :param str url: The original url that came from a service_catalog.

        :returns: Either the unversioned url or the one from the catalog
                  to try.
        """
        for old, new in self._discovery_data.get(service_type, []):
            new_string, number_of_subs_made = old.subn(new, url)
            if number_of_subs_made > 0:
                return new_string

        return url


_VERSION_HACKS = _VersionHacks()
_VERSION_HACKS.add_discover_hack('identity', re.compile('/v2.0/?$'), '/')


def get_catalog_discover_hack(service_type, url):
    """Apply the catalog hacks and figure out an unversioned endpoint.

    This function is internal to keystoneclient.

    :param str service_type: the service_type to look up.
    :param str url: The original url that came from a service_catalog.

    :returns: Either the unversioned url or the one from the catalog to try.
    """
    return _VERSION_HACKS.get_discover_hack(service_type, url)

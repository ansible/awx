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

import datetime

from oslo_utils import timeutils

from keystoneclient import utils

__all__ = ['DiscoveryList',
           'V2Discovery',
           'V3Discovery',
           ]

_DEFAULT_DAYS_AGO = 30


class DiscoveryBase(dict):
    """The basic version discovery structure.

    All version discovery elements should have access to these values.

    :param string id: The version id for this version entry.
    :param string status: The status of this entry.
    :param DateTime updated: When the API was last updated.
    """

    @utils.positional()
    def __init__(self, id, status=None, updated=None):
        super(DiscoveryBase, self).__init__()

        self.id = id
        self.status = status or 'stable'
        self.updated = updated or (timeutils.utcnow() -
                                   datetime.timedelta(days=_DEFAULT_DAYS_AGO))

    @property
    def id(self):
        return self.get('id')

    @id.setter
    def id(self, value):
        self['id'] = value

    @property
    def status(self):
        return self.get('status')

    @status.setter
    def status(self, value):
        self['status'] = value

    @property
    def links(self):
        return self.setdefault('links', [])

    @property
    def updated_str(self):
        return self.get('updated')

    @updated_str.setter
    def updated_str(self, value):
        self['updated'] = value

    @property
    def updated(self):
        return timeutils.parse_isotime(self.updated_str)

    @updated.setter
    def updated(self, value):
        self.updated_str = timeutils.isotime(value)

    @utils.positional()
    def add_link(self, href, rel='self', type=None):
        link = {'href': href, 'rel': rel}
        if type:
            link['type'] = type
        self.links.append(link)
        return link

    @property
    def media_types(self):
        return self.setdefault('media-types', [])

    @utils.positional(1)
    def add_media_type(self, base, type):
        mt = {'base': base, 'type': type}
        self.media_types.append(mt)
        return mt


class V2Discovery(DiscoveryBase):
    """A Version element for a V2 identity service endpoint.

    Provides some default values and helper methods for creating a v2.0
    endpoint version structure. Clients should use this instead of creating
    their own structures.

    :param string href: The url that this entry should point to.
    :param string id: The version id that should be reported. (optional)
                      Defaults to 'v2.0'.
    :param bool html: Add HTML describedby links to the structure.
    :param bool pdf: Add PDF describedby links to the structure.

    """

    _DESC_URL = 'http://docs.openstack.org/api/openstack-identity-service/2.0/'

    @utils.positional()
    def __init__(self, href, id=None, html=True, pdf=True, **kwargs):
        super(V2Discovery, self).__init__(id or 'v2.0', **kwargs)

        self.add_link(href)

        if html:
            self.add_html_description()
        if pdf:
            self.add_pdf_description()

    def add_html_description(self):
        """Add the HTML described by links.

        The standard structure includes a link to a HTML document with the
        API specification. Add it to this entry.
        """
        self.add_link(href=self._DESC_URL + 'content',
                      rel='describedby',
                      type='text/html')

    def add_pdf_description(self):
        """Add the PDF described by links.

        The standard structure includes a link to a PDF document with the
        API specification. Add it to this entry.
        """
        self.add_link(href=self._DESC_URL + 'identity-dev-guide-2.0.pdf',
                      rel='describedby',
                      type='application/pdf')


class V3Discovery(DiscoveryBase):
    """A Version element for a V3 identity service endpoint.

    Provides some default values and helper methods for creating a v3
    endpoint version structure. Clients should use this instead of creating
    their own structures.

    :param href: The url that this entry should point to.
    :param string id: The version id that should be reported. (optional)
                      Defaults to 'v3.0'.
    :param bool json: Add JSON media-type elements to the structure.
    :param bool xml: Add XML media-type elements to the structure.
    """

    @utils.positional()
    def __init__(self, href, id=None, json=True, xml=True, **kwargs):
        super(V3Discovery, self).__init__(id or 'v3.0', **kwargs)

        self.add_link(href)

        if json:
            self.add_json_media_type()
        if xml:
            self.add_xml_media_type()

    def add_json_media_type(self):
        """Add the JSON media-type links.

        The standard structure includes a list of media-types that the endpoint
        supports. Add JSON to the list.
        """
        self.add_media_type(base='application/json',
                            type='application/vnd.openstack.identity-v3+json')

    def add_xml_media_type(self):
        """Add the XML media-type links.

        The standard structure includes a list of media-types that the endpoint
        supports. Add XML to the list.
        """
        self.add_media_type(base='application/xml',
                            type='application/vnd.openstack.identity-v3+xml')


class DiscoveryList(dict):
    """A List of version elements.

    Creates a correctly structured list of identity service endpoints for
    use in testing with discovery.

    :param string href: The url that this should be based at.
    :param bool v2: Add a v2 element.
    :param bool v3: Add a v3 element.
    :param string v2_status: The status to use for the v2 element.
    :param DateTime v2_updated: The update time to use for the v2 element.
    :param bool v2_html: True to add a html link to the v2 element.
    :param bool v2_pdf: True to add a pdf link to the v2 element.
    :param string v3_status: The status to use for the v3 element.
    :param DateTime v3_updated: The update time to use for the v3 element.
    :param bool v3_json: True to add a html link to the v2 element.
    :param bool v3_xml: True to add a pdf link to the v2 element.
    """

    TEST_URL = 'http://keystone.host:5000/'

    @utils.positional(2)
    def __init__(self, href=None, v2=True, v3=True, v2_id=None, v3_id=None,
                 v2_status=None, v2_updated=None, v2_html=True, v2_pdf=True,
                 v3_status=None, v3_updated=None, v3_json=True, v3_xml=True):
        super(DiscoveryList, self).__init__(versions={'values': []})

        href = href or self.TEST_URL

        if v2:
            v2_href = href.rstrip('/') + '/v2.0'
            self.add_v2(v2_href, id=v2_id, status=v2_status,
                        updated=v2_updated, html=v2_html, pdf=v2_pdf)

        if v3:
            v3_href = href.rstrip('/') + '/v3'
            self.add_v3(v3_href, id=v3_id, status=v3_status,
                        updated=v3_updated, json=v3_json, xml=v3_xml)

    @property
    def versions(self):
        return self['versions']['values']

    def add_version(self, version):
        """Add a new version structure to the list.

        :param dict version: A new version structure to add to the list.
        """
        self.versions.append(version)

    def add_v2(self, href, **kwargs):
        """Add a v2 version to the list.

        The parameters are the same as V2Discovery.
        """
        obj = V2Discovery(href, **kwargs)
        self.add_version(obj)
        return obj

    def add_v3(self, href, **kwargs):
        """Add a v3 version to the list.

        The parameters are the same as V3Discovery.
        """
        obj = V3Discovery(href, **kwargs)
        self.add_version(obj)
        return obj

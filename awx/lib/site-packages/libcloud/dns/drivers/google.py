# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__all__ = [
    'GoogleDNSDriver'
]

API_VERSION = 'v1beta1'

import re
from libcloud.common.google import GoogleResponse, GoogleBaseConnection
from libcloud.common.google import ResourceNotFoundError
from libcloud.dns.types import Provider, RecordType
from libcloud.dns.types import ZoneDoesNotExistError, RecordDoesNotExistError
from libcloud.dns.base import DNSDriver, Zone, Record


class GoogleDNSResponse(GoogleResponse):
    pass


class GoogleDNSConnection(GoogleBaseConnection):
    host = "www.googleapis.com"
    responseCls = GoogleDNSResponse

    def __init__(self, user_id, key, secure, auth_type=None,
                 credential_file=None, project=None, **kwargs):
        super(GoogleDNSConnection, self).\
            __init__(user_id, key, secure=secure, auth_type=auth_type,
                     credential_file=credential_file, **kwargs)
        self.request_path = '/dns/%s/projects/%s' % (API_VERSION, project)


class GoogleDNSDriver(DNSDriver):
    type = Provider.GOOGLE
    name = 'Google DNS'
    connectionCls = GoogleDNSConnection
    website = 'https://cloud.google.com/'

    RECORD_TYPE_MAP = {
        RecordType.A: 'A',
        RecordType.AAAA: 'AAAA',
        RecordType.CNAME: 'CNAME',
        RecordType.MX: 'MX',
        RecordType.NS: 'NS',
        RecordType.PTR: 'PTR',
        RecordType.SOA: 'SOA',
        RecordType.SPF: 'SPF',
        RecordType.SRV: 'SRV',
        RecordType.TXT: 'TXT',
    }

    def __init__(self, user_id, key, project=None, auth_type=None, scopes=None,
                 **kwargs):
        self.auth_type = auth_type
        self.project = project
        self.scopes = scopes
        if not self.project:
            raise ValueError('Project name must be specified using '
                             '"project" keyword.')
        super(GoogleDNSDriver, self).__init__(user_id, key, scopes, **kwargs)

    def iterate_zones(self):
        """
        Return a generator to iterate over available zones.

        :rtype: ``generator`` of :class:`Zone`
        """
        return self._get_more('zones')

    def iterate_records(self, zone):
        """
        Return a generator to iterate over records for the provided zone.

        :param zone: Zone to list records for.
        :type zone: :class:`Zone`

        :rtype: ``generator`` of :class:`Record`
        """
        return self._get_more('records', zone=zone)

    def get_zone(self, zone_id):
        """
        Return a Zone instance.

        :param zone_id: ID of the required zone
        :type  zone_id: ``str``

        :rtype: :class:`Zone`
        """
        request = '/managedZones/%s' % (zone_id)

        try:
            response = self.connection.request(request, method='GET').object
        except ResourceNotFoundError:
            raise ZoneDoesNotExistError(value='',
                                        driver=self.connection.driver,
                                        zone_id=zone_id)

        return self._to_zone(response)

    def get_record(self, zone_id, record_id):
        """
        Return a Record instance.

        :param zone_id: ID of the required zone
        :type  zone_id: ``str``

        :param record_id: ID of the required record
        :type  record_id: ``str``

        :rtype: :class:`Record`
        """
        (record_type, record_name) = record_id.split(':', 1)

        params = {
            'name': record_name,
            'type': record_type,
        }

        request = '/managedZones/%s/rrsets' % (zone_id)

        try:
            response = self.connection.request(request, method='GET',
                                               params=params).object
        except ResourceNotFoundError:
            raise ZoneDoesNotExistError(value='',
                                        driver=self.connection.driver,
                                        zone_id=zone_id)

        if len(response['rrsets']) > 0:
            zone = self.get_zone(zone_id)
            return self._to_record(response['rrsets'][0], zone)

        raise RecordDoesNotExistError(value='', driver=self.connection.driver,
                                      record_id=record_id)

    def create_zone(self, domain, type='master', ttl=None, extra=None):
        """
        Create a new zone.

        :param domain: Zone domain name (e.g. example.com.) with a \'.\'
                       at the end.
        :type domain: ``str``

        :param type: Zone type (master is the only one supported).
        :type  type: ``str``

        :param ttl: TTL for new records. (unused)
        :type  ttl: ``int``

        :param extra: Extra attributes (driver specific). (optional)
        :type extra: ``dict``

        :rtype: :class:`Zone`
        """
        name = None
        description = ''

        if extra:
            description = extra.get('description')
            name = extra.get('name')

        if name is None:
            name = self._cleanup_domain(domain)

        data = {
            'dnsName': domain,
            'name': name,
            'description': description,
        }

        request = '/managedZones'
        response = self.connection.request(request, method='POST',
                                           data=data).object
        return self._to_zone(response)

    def create_record(self, name, zone, type, data, extra=None):
        """
        Create a new record.

        :param name: Record name fully qualified, with a \'.\' at the end.
        :type  name: ``str``

        :param zone: Zone where the requested record is created.
        :type  zone: :class:`Zone`

        :param type: DNS record type (A, AAAA, ...).
        :type  type: :class:`RecordType`

        :param data: Data for the record (depends on the record type).
        :type  data: ``str``

        :param extra: Extra attributes. (optional)
        :type extra: ``dict``

        :rtype: :class:`Record`
        """
        ttl = data.get('ttl', None)
        rrdatas = data.get('rrdatas', [])

        data = {
            'additions': [
                {
                    'name': name,
                    'type': type,
                    'ttl': int(ttl),
                    'rrdatas': rrdatas,
                }
            ]
        }
        request = '/managedZones/%s/changes' % (zone.id)
        response = self.connection.request(request, method='POST',
                                           data=data).object
        return self._to_record(response['additions'][0], zone)

    def delete_zone(self, zone):
        """
        Delete a zone.

        Note: This will delete all the records belonging to this zone.

        :param zone: Zone to delete.
        :type  zone: :class:`Zone`

        :rtype: ``bool``
        """
        request = '/managedZones/%s' % (zone.id)
        response = self.connection.request(request, method='DELETE')
        return response.success()

    def delete_record(self, record):
        """
        Delete a record.

        :param record: Record to delete.
        :type  record: :class:`Record`

        :rtype: ``bool``
        """
        data = {
            'deletions': [
                {
                    'name': record.name,
                    'type': record.type,
                    'rrdatas': record.data['rrdatas'],
                    'ttl': record.data['ttl']
                }
            ]
        }
        request = '/managedZones/%s/changes' % (record.zone.id)
        response = self.connection.request(request, method='POST',
                                           data=data)
        return response.success()

    def _get_more(self, rtype, **kwargs):
        last_key = None
        exhausted = False
        while not exhausted:
            items, last_key, exhausted = self._get_data(rtype, last_key,
                                                        **kwargs)
            for item in items:
                yield item

    def _get_data(self, rtype, last_key, **kwargs):
        params = {}

        if last_key:
            params['pageToken'] = last_key

        if rtype == 'zones':
            request = '/managedZones'
            transform_func = self._to_zones
            r_key = 'managedZones'
        elif rtype == 'records':
            zone = kwargs['zone']
            request = '/managedZones/%s/rrsets' % (zone.id)
            transform_func = self._to_records
            r_key = 'rrsets'

        response = self.connection.request(request, method='GET',
                                           params=params,)

        if response.success():
            nextpage = response.object.get('nextPageToken', None)
            items = transform_func(response.object.get(r_key), **kwargs)
            exhausted = False if nextpage is not None else True
            return items, nextpage, exhausted
        else:
            return [], None, True

    def _ex_connection_class_kwargs(self):
        return {'auth_type': self.auth_type,
                'project': self.project,
                'scopes': self.scopes}

    def _to_zones(self, response):
        zones = []
        for r in response:
            zones.append(self._to_zone(r))
        return zones

    def _to_zone(self, r):
        extra = {}

        if 'description' in r:
            extra['description'] = r.get('description')

        extra['creationTime'] = r.get('creationTime')
        extra['nameServers'] = r.get('nameServers')
        extra['id'] = r.get('id')

        return Zone(id=r['name'], domain=r['dnsName'],
                    type='master', ttl=0, driver=self, extra=extra)

    def _to_records(self, response, zone):
        records = []
        for r in response:
            records.append(self._to_record(r, zone))
        return records

    def _to_record(self, r, zone):
        record_id = '%s:%s' % (r['type'], r['name'])
        return Record(id=record_id, name=r['name'],
                      type=r['type'], data=r, zone=zone,
                      driver=self, extra={})

    def _cleanup_domain(self, domain):
        # name can only contain lower case alphanumeric characters and hyphens
        domain = re.sub(r'[^a-zA-Z0-9-]', '-', domain)
        if domain[-1] == '-':
            domain = domain[:-1]
        return domain

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
    'LinodeDNSDriver'
]

from libcloud.utils.misc import merge_valid_keys, get_new_obj
from libcloud.common.linode import (API_ROOT, LinodeException,
                                    LinodeConnection, LinodeResponse)
from libcloud.dns.types import Provider, RecordType
from libcloud.dns.types import ZoneDoesNotExistError, RecordDoesNotExistError
from libcloud.dns.base import DNSDriver, Zone, Record


VALID_ZONE_EXTRA_PARAMS = ['SOA_Email', 'Refresh_sec', 'Retry_sec',
                           'Expire_sec', 'status', 'master_ips']

VALID_RECORD_EXTRA_PARAMS = ['Priority', 'Weight', 'Port', 'Protocol',
                             'TTL_sec']


class LinodeDNSResponse(LinodeResponse):
    def _make_excp(self, error):
        result = super(LinodeDNSResponse, self)._make_excp(error)
        if isinstance(result, LinodeException) and result.code == 5:
            context = self.connection.context

            if context['resource'] == 'zone':
                result = ZoneDoesNotExistError(value='',
                                               driver=self.connection.driver,
                                               zone_id=context['id'])

            elif context['resource'] == 'record':
                result = RecordDoesNotExistError(value='',
                                                 driver=self.connection.driver,
                                                 record_id=context['id'])
        return result


class LinodeDNSConnection(LinodeConnection):
    responseCls = LinodeDNSResponse


class LinodeDNSDriver(DNSDriver):
    type = Provider.LINODE
    name = 'Linode DNS'
    website = 'http://www.linode.com/'
    connectionCls = LinodeDNSConnection

    RECORD_TYPE_MAP = {
        RecordType.NS: 'NS',
        RecordType.MX: 'MX',
        RecordType.A: 'A',
        RecordType.AAAA: 'AAAA',
        RecordType.CNAME: 'CNAME',
        RecordType.TXT: 'TXT',
        RecordType.SRV: 'SRV',
    }

    def list_zones(self):
        params = {'api_action': 'domain.list'}
        data = self.connection.request(API_ROOT, params=params).objects[0]
        zones = self._to_zones(data)
        return zones

    def list_records(self, zone):
        params = {'api_action': 'domain.resource.list', 'DOMAINID': zone.id}

        self.connection.set_context(context={'resource': 'zone',
                                             'id': zone.id})
        data = self.connection.request(API_ROOT, params=params).objects[0]
        records = self._to_records(items=data, zone=zone)
        return records

    def get_zone(self, zone_id):
        params = {'api_action': 'domain.list', 'DomainID': zone_id}
        self.connection.set_context(context={'resource': 'zone',
                                             'id': zone_id})
        data = self.connection.request(API_ROOT, params=params).objects[0]
        zones = self._to_zones(data)

        if len(zones) != 1:
            raise ZoneDoesNotExistError(value='', driver=self, zone_id=zone_id)

        return zones[0]

    def get_record(self, zone_id, record_id):
        zone = self.get_zone(zone_id=zone_id)
        params = {'api_action': 'domain.resource.list', 'DomainID': zone_id,
                  'ResourceID': record_id}
        self.connection.set_context(context={'resource': 'record',
                                             'id': record_id})
        data = self.connection.request(API_ROOT, params=params).objects[0]
        records = self._to_records(items=data, zone=zone)

        if len(records) != 1:
            raise RecordDoesNotExistError(value='', driver=self,
                                          record_id=record_id)

        return records[0]

    def create_zone(self, domain, type='master', ttl=None, extra=None):
        """
        Create a new zone.

        API docs: http://www.linode.com/api/dns/domain.create
        """
        params = {'api_action': 'domain.create', 'Type': type,
                  'Domain': domain}

        if ttl:
            params['TTL_sec'] = ttl

        merged = merge_valid_keys(params=params,
                                  valid_keys=VALID_ZONE_EXTRA_PARAMS,
                                  extra=extra)
        data = self.connection.request(API_ROOT, params=params).objects[0]
        zone = Zone(id=data['DomainID'], domain=domain, type=type, ttl=ttl,
                    extra=merged, driver=self)
        return zone

    def update_zone(self, zone, domain=None, type=None, ttl=None, extra=None):
        """
        Update an existing zone.

        API docs: http://www.linode.com/api/dns/domain.update
        """
        params = {'api_action': 'domain.update', 'DomainID': zone.id}

        if type:
            params['Type'] = type

        if domain:
            params['Domain'] = domain

        if ttl:
            params['TTL_sec'] = ttl

        merged = merge_valid_keys(params=params,
                                  valid_keys=VALID_ZONE_EXTRA_PARAMS,
                                  extra=extra)
        self.connection.request(API_ROOT, params=params).objects[0]
        updated_zone = get_new_obj(obj=zone, klass=Zone,
                                   attributes={'domain': domain,
                                               'type': type, 'ttl': ttl,
                                               'extra': merged})
        return updated_zone

    def create_record(self, name, zone, type, data, extra=None):
        """
        Create a new record.

        API docs: http://www.linode.com/api/dns/domain.resource.create
        """
        params = {'api_action': 'domain.resource.create', 'DomainID': zone.id,
                  'Name': name, 'Target': data,
                  'Type': self.RECORD_TYPE_MAP[type]}
        merged = merge_valid_keys(params=params,
                                  valid_keys=VALID_RECORD_EXTRA_PARAMS,
                                  extra=extra)

        result = self.connection.request(API_ROOT, params=params).objects[0]
        record = Record(id=result['ResourceID'], name=name, type=type,
                        data=data, extra=merged, zone=zone, driver=self)
        return record

    def update_record(self, record, name=None, type=None, data=None,
                      extra=None):
        """
        Update an existing record.

        API docs: http://www.linode.com/api/dns/domain.resource.update
        """
        params = {'api_action': 'domain.resource.update',
                  'ResourceID': record.id, 'DomainID': record.zone.id}

        if name:
            params['Name'] = name

        if data:
            params['Target'] = data

        if type is not None:
            params['Type'] = self.RECORD_TYPE_MAP[type]

        merged = merge_valid_keys(params=params,
                                  valid_keys=VALID_RECORD_EXTRA_PARAMS,
                                  extra=extra)

        self.connection.request(API_ROOT, params=params).objects[0]
        updated_record = get_new_obj(obj=record, klass=Record,
                                     attributes={'name': name, 'data': data,
                                                 'type': type,
                                                 'extra': merged})
        return updated_record

    def delete_zone(self, zone):
        params = {'api_action': 'domain.delete', 'DomainID': zone.id}

        self.connection.set_context(context={'resource': 'zone',
                                             'id': zone.id})
        data = self.connection.request(API_ROOT, params=params).objects[0]

        return 'DomainID' in data

    def delete_record(self, record):
        params = {'api_action': 'domain.resource.delete',
                  'DomainID': record.zone.id, 'ResourceID': record.id}

        self.connection.set_context(context={'resource': 'record',
                                             'id': record.id})
        data = self.connection.request(API_ROOT, params=params).objects[0]

        return 'ResourceID' in data

    def _to_zones(self, items):
        """
        Convert a list of items to the Zone objects.
        """
        zones = []

        for item in items:
            zones.append(self._to_zone(item))

        return zones

    def _to_zone(self, item):
        """
        Build an Zone object from the item dictionary.
        """
        extra = {'SOA_Email': item['SOA_EMAIL'], 'status': item['STATUS'],
                 'description': item['DESCRIPTION']}
        zone = Zone(id=item['DOMAINID'], domain=item['DOMAIN'],
                    type=item['TYPE'], ttl=item['TTL_SEC'], driver=self,
                    extra=extra)
        return zone

    def _to_records(self, items, zone=None):
        """
        Convert a list of items to the Record objects.
        """
        records = []

        for item in items:
            records.append(self._to_record(item=item, zone=zone))

        return records

    def _to_record(self, item, zone=None):
        """
        Build a Record object from the item dictionary.
        """
        extra = {'protocol': item['PROTOCOL'], 'ttl_sec': item['TTL_SEC'],
                 'port': item['PORT'], 'weight': item['WEIGHT']}
        type = self._string_to_record_type(item['TYPE'])
        record = Record(id=item['RESOURCEID'], name=item['NAME'], type=type,
                        data=item['TARGET'], zone=zone, driver=self,
                        extra=extra)
        return record

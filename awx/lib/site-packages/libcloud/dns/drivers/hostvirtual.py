# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__all__ = [
    'HostVirtualDNSDriver'
]

from libcloud.utils.py3 import httplib
from libcloud.utils.misc import merge_valid_keys, get_new_obj
from libcloud.common.hostvirtual import HostVirtualResponse
from libcloud.common.hostvirtual import HostVirtualConnection
from libcloud.compute.drivers.hostvirtual import API_ROOT
from libcloud.dns.types import Provider, RecordType
from libcloud.dns.types import ZoneDoesNotExistError, RecordDoesNotExistError
from libcloud.dns.base import DNSDriver, Zone, Record

try:
    import simplejson as json
except:
    import json

VALID_RECORD_EXTRA_PARAMS = ['prio', 'ttl']


class HostVirtualDNSResponse(HostVirtualResponse):
    def parse_error(self):
        context = self.connection.context
        status = int(self.status)

        if status == httplib.NOT_FOUND:
            if context['resource'] == 'zone':
                raise ZoneDoesNotExistError(value='', driver=self,
                                            zone_id=context['id'])
            elif context['resource'] == 'record':
                raise RecordDoesNotExistError(value='', driver=self,
                                              record_id=context['id'])

        super(HostVirtualDNSResponse, self).parse_error()
        return self.body


class HostVirtualDNSConnection(HostVirtualConnection):
    responseCls = HostVirtualDNSResponse


class HostVirtualDNSDriver(DNSDriver):
    type = Provider.HOSTVIRTUAL
    name = 'Host Virtual DNS'
    website = 'http://www.vr.org/'
    connectionCls = HostVirtualDNSConnection

    RECORD_TYPE_MAP = {
        RecordType.A: 'A',
        RecordType.AAAA: 'AAAA',
        RecordType.CNAME: 'CNAME',
        RecordType.MX: 'MX',
        RecordType.NS: 'SPF',
        RecordType.SRV: 'SRV',
        RecordType.TXT: 'TXT',
    }

    def __init__(self, key, secure=True, host=None, port=None):
        super(HostVirtualDNSDriver, self).__init__(key=key, secure=secure,
                                                   host=host, port=port)

    def _to_zones(self, items):
        zones = []
        for item in items:
            zones.append(self._to_zone(item))
        return zones

    def _to_zone(self, item):
        extra = {}
        if 'records' in item:
            extra['records'] = item['records']
        if item['type'] == 'NATIVE':
            item['type'] = 'master'
        zone = Zone(id=item['id'], domain=item['name'],
                    type=item['type'], ttl=item['ttl'],
                    driver=self, extra=extra)
        return zone

    def _to_records(self, items, zone=None):
        records = []

        for item in items:
            records.append(self._to_record(item=item, zone=zone))
        return records

    def _to_record(self, item, zone=None):
        extra = {'ttl': item['ttl']}
        type = self._string_to_record_type(item['type'])
        record = Record(id=item['id'], name=item['name'],
                        type=type, data=item['content'],
                        zone=zone, driver=self, extra=extra)
        return record

    def list_zones(self):
        result = self.connection.request(
            API_ROOT + '/dns/zones/').object
        zones = self._to_zones(result)
        return zones

    def list_records(self, zone):
        params = {'id': zone.id}
        self.connection.set_context({'resource': 'zone', 'id': zone.id})
        result = self.connection.request(
            API_ROOT + '/dns/records/', params=params).object
        records = self._to_records(items=result, zone=zone)
        return records

    def get_zone(self, zone_id):
        params = {'id': zone_id}
        self.connection.set_context({'resource': 'zone', 'id': zone_id})
        result = self.connection.request(
            API_ROOT + '/dns/zone/', params=params).object
        if 'id' not in result:
            raise ZoneDoesNotExistError(value='', driver=self, zone_id=zone_id)
        zone = self._to_zone(result)
        return zone

    def get_record(self, zone_id, record_id):
        zone = self.get_zone(zone_id=zone_id)
        params = {'id': record_id}
        self.connection.set_context({'resource': 'record', 'id': record_id})
        result = self.connection.request(
            API_ROOT + '/dns/record/', params=params).object
        if 'id' not in result:
            raise RecordDoesNotExistError(value='',
                                          driver=self, record_id=record_id)
        record = self._to_record(item=result, zone=zone)
        return record

    def delete_zone(self, zone):
        params = {'zone_id': zone.id}
        self.connection.set_context({'resource': 'zone', 'id': zone.id})
        result = self.connection.request(
            API_ROOT + '/dns/zone/', params=params, method='DELETE').object
        return bool(result)

    def delete_record(self, record):
        params = {'id': record.id}
        self.connection.set_context({'resource': 'record', 'id': record.id})
        result = self.connection.request(
            API_ROOT + '/dns/record/', params=params, method='DELETE').object

        return bool(result)

    def create_zone(self, domain, type='NATIVE', ttl=None, extra=None):
        if type == 'master':
            type = 'NATIVE'
        elif type == 'slave':
            type = 'SLAVE'
        params = {'name': domain, 'type': type, 'ttl': ttl}
        result = self.connection.request(
            API_ROOT + '/dns/zone/',
            data=json.dumps(params), method='POST').object
        extra = {
            'soa': result['soa'],
            'ns': result['ns']
        }
        zone = Zone(id=result['id'], domain=domain,
                    type=type, ttl=ttl, extra=extra, driver=self)
        return zone

    def update_zone(self, zone, domain=None, type=None, ttl=None, extra=None):
        params = {'id': zone.id}
        if domain:
            params['name'] = domain
        if type:
            params['type'] = type
        self.connection.set_context({'resource': 'zone', 'id': zone.id})
        self.connection.request(API_ROOT + '/dns/zone/',
                                data=json.dumps(params), method='PUT').object
        updated_zone = get_new_obj(
            obj=zone, klass=Zone,
            attributes={
                'domain': domain,
                'type': type,
                'ttl': ttl,
                'extra': extra
            })
        return updated_zone

    def create_record(self, name, zone, type, data, extra=None):
        params = {
            'name': name,
            'type': self.RECORD_TYPE_MAP[type],
            'domain_id': zone.id,
            'content': data
        }
        merged = merge_valid_keys(
            params=params,
            valid_keys=VALID_RECORD_EXTRA_PARAMS,
            extra=extra
        )
        self.connection.set_context({'resource': 'zone', 'id': zone.id})
        result = self.connection.request(
            API_ROOT + '/dns/record/',
            data=json.dumps(params), method='POST').object
        record = Record(id=result['id'], name=name,
                        type=type, data=data,
                        extra=merged, zone=zone, driver=self)
        return record

    def update_record(self, record, name=None, type=None,
                      data=None, extra=None):
        params = {
            'domain_id': record.zone.id,
            'record_id': record.id
        }
        if name:
            params['name'] = name
        if data:
            params['content'] = data
        if type is not None:
            params['type'] = self.RECORD_TYPE_MAP[type]
            merged = merge_valid_keys(
                params=params,
                valid_keys=VALID_RECORD_EXTRA_PARAMS,
                extra=extra
            )
        self.connection.set_context({'resource': 'record', 'id': record.id})
        self.connection.request(API_ROOT + '/dns/record/',
                                data=json.dumps(params), method='PUT').object
        updated_record = get_new_obj(
            obj=record, klass=Record, attributes={
                'name': name, 'data': data,
                'type': type,
                'extra': merged
            })
        return updated_record

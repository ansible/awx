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

from __future__ import with_statement

__all__ = [
    'GandiDNSDriver'
]

from libcloud.common.gandi import BaseGandiDriver, GandiConnection
from libcloud.common.gandi import GandiResponse
from libcloud.dns.types import Provider, RecordType
from libcloud.dns.types import RecordError
from libcloud.dns.types import ZoneDoesNotExistError, RecordDoesNotExistError
from libcloud.dns.base import DNSDriver, Zone, Record


TTL_MIN = 30
TTL_MAX = 2592000  # 30 days


class NewZoneVersion(object):
    """
    Changes to a zone in the Gandi DNS service need to be wrapped in a new
    version object. The changes are made to the new version, then that
    version is made active.

    In effect, this is a transaction.

    Any calls made inside this context manager will be applied to a new version
    id. If your changes are succesful (and only if they are successful) they
    are activated.
    """

    def __init__(self, driver, zone):
        self.driver = driver
        self.connection = driver.connection
        self.zone = zone

    def __enter__(self):
        zid = int(self.zone.id)
        self.connection.set_context({'zone_id': self.zone.id})
        vid = self.connection.request('domain.zone.version.new', zid).object
        self.vid = vid
        return vid

    def __exit__(self, type, value, traceback):
        if not traceback:
            zid = int(self.zone.id)
            con = self.connection
            con.set_context({'zone_id': self.zone.id})
            con.request('domain.zone.version.set', zid, self.vid).object


class GandiDNSResponse(GandiResponse):
    exceptions = {
        581042: ZoneDoesNotExistError,
    }


class GandiDNSConnection(GandiConnection):
    responseCls = GandiDNSResponse


class GandiDNSDriver(BaseGandiDriver, DNSDriver):
    """
    API reference can be found at:

    http://doc.rpc.gandi.net/domain/reference.html
    """

    type = Provider.GANDI
    name = 'Gandi DNS'
    website = 'http://www.gandi.net/domain'

    connectionCls = GandiDNSConnection

    RECORD_TYPE_MAP = {
        RecordType.A: 'A',
        RecordType.AAAA: 'AAAA',
        RecordType.CNAME: 'CNAME',
        RecordType.LOC: 'LOC',
        RecordType.MX: 'MX',
        RecordType.NS: 'NS',
        RecordType.SPF: 'SPF',
        RecordType.SRV: 'SRV',
        RecordType.TXT: 'TXT',
        RecordType.WKS: 'WKS',
    }

    def _to_zone(self, zone):
        return Zone(
            id=str(zone['id']),
            domain=zone['name'],
            type='master',
            ttl=0,
            driver=self,
            extra={}
        )

    def _to_zones(self, zones):
        ret = []
        for z in zones:
            ret.append(self._to_zone(z))
        return ret

    def list_zones(self):
        zones = self.connection.request('domain.zone.list')
        return self._to_zones(zones.object)

    def get_zone(self, zone_id):
        zid = int(zone_id)
        self.connection.set_context({'zone_id': zone_id})
        zone = self.connection.request('domain.zone.info', zid)
        return self._to_zone(zone.object)

    def create_zone(self, domain, type='master', ttl=None, extra=None):
        params = {
            'name': domain,
        }
        info = self.connection.request('domain.zone.create', params)
        return self._to_zone(info.object)

    def update_zone(self, zone, domain=None, type=None, ttl=None, extra=None):
        zid = int(zone.id)
        params = {'name': domain}
        self.connection.set_context({'zone_id': zone.id})
        zone = self.connection.request('domain.zone.update', zid, params)
        return self._to_zone(zone.object)

    def delete_zone(self, zone):
        zid = int(zone.id)
        self.connection.set_context({'zone_id': zone.id})
        res = self.connection.request('domain.zone.delete', zid)
        return res.object

    def _to_record(self, record, zone):
        return Record(
            id='%s:%s' % (record['type'], record['name']),
            name=record['name'],
            type=self._string_to_record_type(record['type']),
            data=record['value'],
            zone=zone,
            driver=self,
            extra={'ttl': record['ttl']}
        )

    def _to_records(self, records, zone):
        retval = []
        for r in records:
            retval.append(self._to_record(r, zone))
        return retval

    def list_records(self, zone):
        zid = int(zone.id)
        self.connection.set_context({'zone_id': zone.id})
        records = self.connection.request('domain.zone.record.list', zid, 0)
        return self._to_records(records.object, zone)

    def get_record(self, zone_id, record_id):
        zid = int(zone_id)
        record_type, name = record_id.split(':', 1)
        filter_opts = {
            'name': name,
            'type': record_type
        }
        self.connection.set_context({'zone_id': zone_id})
        records = self.connection.request('domain.zone.record.list',
                                          zid, 0, filter_opts).object

        if len(records) == 0:
            raise RecordDoesNotExistError(value='', driver=self,
                                          record_id=record_id)

        return self._to_record(records[0], self.get_zone(zone_id))

    def _validate_record(self, record_id, name, record_type, data, extra):
        if len(data) > 1024:
            raise RecordError('Record data must be <= 1024 characters',
                              driver=self, record_id=record_id)
        if extra and 'ttl' in extra:
            if extra['ttl'] < TTL_MIN:
                raise RecordError('TTL must be at least 30 seconds',
                                  driver=self, record_id=record_id)
            if extra['ttl'] > TTL_MAX:
                raise RecordError('TTL must not excdeed 30 days',
                                  driver=self, record_id=record_id)

    def create_record(self, name, zone, type, data, extra=None):
        self._validate_record(None, name, type, data, extra)

        zid = int(zone.id)

        create = {
            'name': name,
            'type': self.RECORD_TYPE_MAP[type],
            'value': data
        }

        if 'ttl' in extra:
            create['ttl'] = extra['ttl']

        with NewZoneVersion(self, zone) as vid:
            con = self.connection
            con.set_context({'zone_id': zone.id})
            rec = con.request('domain.zone.record.add',
                              zid, vid, create).object

        return self._to_record(rec, zone)

    def update_record(self, record, name, type, data, extra):
        self._validate_record(record.id, name, type, data, extra)

        filter_opts = {
            'name': record.name,
            'type': self.RECORD_TYPE_MAP[record.type]
        }

        update = {
            'name': name,
            'type': self.RECORD_TYPE_MAP[type],
            'value': data
        }

        if 'ttl' in extra:
            update['ttl'] = extra['ttl']

        zid = int(record.zone.id)

        with NewZoneVersion(self, record.zone) as vid:
            con = self.connection
            con.set_context({'zone_id': record.zone.id})
            con.request('domain.zone.record.delete',
                        zid, vid, filter_opts)
            res = con.request('domain.zone.record.add',
                              zid, vid, update).object

        return self._to_record(res, record.zone)

    def delete_record(self, record):
        zid = int(record.zone.id)

        filter_opts = {
            'name': record.name,
            'type': self.RECORD_TYPE_MAP[record.type]
        }

        with NewZoneVersion(self, record.zone) as vid:
            con = self.connection
            con.set_context({'zone_id': record.zone.id})
            count = con.request('domain.zone.record.delete',
                                zid, vid, filter_opts).object

        if count == 1:
            return True

        raise RecordDoesNotExistError(value='No such record', driver=self,
                                      record_id=record.id)

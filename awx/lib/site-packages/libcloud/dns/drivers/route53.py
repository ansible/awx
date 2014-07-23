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
    'Route53DNSDriver'
]

import base64
import hmac
import datetime
import uuid
import copy
from libcloud.utils.py3 import httplib

from hashlib import sha1

try:
    from lxml import etree as ET
except ImportError:
    from xml.etree import ElementTree as ET

from libcloud.utils.py3 import b, urlencode

from libcloud.utils.xml import findtext, findall, fixxpath
from libcloud.dns.types import Provider, RecordType
from libcloud.dns.types import ZoneDoesNotExistError, RecordDoesNotExistError
from libcloud.dns.base import DNSDriver, Zone, Record
from libcloud.common.types import LibcloudError
from libcloud.common.aws import AWSGenericResponse
from libcloud.common.base import ConnectionUserAndKey


API_VERSION = '2012-02-29'
API_HOST = 'route53.amazonaws.com'
API_ROOT = '/%s/' % (API_VERSION)

NAMESPACE = 'https://%s/doc%s' % (API_HOST, API_ROOT)


class InvalidChangeBatch(LibcloudError):
    pass


class Route53DNSResponse(AWSGenericResponse):
    """
    Amazon Route53 response class.
    """

    namespace = NAMESPACE
    xpath = 'Error'

    exceptions = {
        'NoSuchHostedZone': ZoneDoesNotExistError,
        'InvalidChangeBatch': InvalidChangeBatch,
    }


class Route53Connection(ConnectionUserAndKey):
    host = API_HOST
    responseCls = Route53DNSResponse

    def pre_connect_hook(self, params, headers):
        time_string = datetime.datetime.utcnow() \
                              .strftime('%a, %d %b %Y %H:%M:%S GMT')
        headers['Date'] = time_string
        tmp = []

        signature = self._get_aws_auth_b64(self.key, time_string)
        auth = {'AWSAccessKeyId': self.user_id, 'Signature': signature,
                'Algorithm': 'HmacSHA1'}

        for k, v in auth.items():
            tmp.append('%s=%s' % (k, v))

        headers['X-Amzn-Authorization'] = 'AWS3-HTTPS ' + ','.join(tmp)

        return params, headers

    def _get_aws_auth_b64(self, secret_key, time_string):
        b64_hmac = base64.b64encode(
            hmac.new(b(secret_key), b(time_string), digestmod=sha1).digest()
        )

        return b64_hmac.decode('utf-8')


class Route53DNSDriver(DNSDriver):
    type = Provider.ROUTE53
    name = 'Route53 DNS'
    website = 'http://aws.amazon.com/route53/'
    connectionCls = Route53Connection

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

    def iterate_zones(self):
        return self._get_more('zones')

    def iterate_records(self, zone):
        return self._get_more('records', zone=zone)

    def get_zone(self, zone_id):
        self.connection.set_context({'zone_id': zone_id})
        uri = API_ROOT + 'hostedzone/' + zone_id
        data = self.connection.request(uri).object
        elem = findall(element=data, xpath='HostedZone',
                       namespace=NAMESPACE)[0]
        return self._to_zone(elem)

    def get_record(self, zone_id, record_id):
        zone = self.get_zone(zone_id=zone_id)
        record_type, name = record_id.split(':', 1)
        if name:
            full_name = ".".join((name, zone.domain))
        else:
            full_name = zone.domain
        self.connection.set_context({'zone_id': zone_id})
        params = urlencode({
            'name': full_name,
            'type': record_type,
            'maxitems': '1'
        })
        uri = API_ROOT + 'hostedzone/' + zone_id + '/rrset?' + params
        data = self.connection.request(uri).object

        record = self._to_records(data=data, zone=zone)[0]

        # A cute aspect of the /rrset filters is that they are more pagination
        # hints than filters!!
        # So will return a result even if its not what you asked for.
        record_type_num = self._string_to_record_type(record_type)
        if record.name != name or record.type != record_type_num:
            raise RecordDoesNotExistError(value='', driver=self,
                                          record_id=record_id)

        return record

    def create_zone(self, domain, type='master', ttl=None, extra=None):
        zone = ET.Element('CreateHostedZoneRequest', {'xmlns': NAMESPACE})
        ET.SubElement(zone, 'Name').text = domain
        ET.SubElement(zone, 'CallerReference').text = str(uuid.uuid4())

        if extra and 'Comment' in extra:
            hzg = ET.SubElement(zone, 'HostedZoneConfig')
            ET.SubElement(hzg, 'Comment').text = extra['Comment']

        uri = API_ROOT + 'hostedzone'
        data = ET.tostring(zone)
        rsp = self.connection.request(uri, method='POST', data=data).object

        elem = findall(element=rsp, xpath='HostedZone', namespace=NAMESPACE)[0]
        return self._to_zone(elem=elem)

    def delete_zone(self, zone, ex_delete_records=False):
        self.connection.set_context({'zone_id': zone.id})

        if ex_delete_records:
            self.ex_delete_all_records(zone=zone)

        uri = API_ROOT + 'hostedzone/%s' % (zone.id)
        response = self.connection.request(uri, method='DELETE')
        return response.status in [httplib.OK]

    def create_record(self, name, zone, type, data, extra=None):
        extra = extra or {}
        batch = [('CREATE', name, type, data, extra)]
        self._post_changeset(zone, batch)
        id = ':'.join((self.RECORD_TYPE_MAP[type], name))
        return Record(id=id, name=name, type=type, data=data, zone=zone,
                      driver=self, extra=extra)

    def update_record(self, record, name=None, type=None, data=None,
                      extra=None):
        name = name or record.name
        type = type or record.type
        extra = extra or record.extra

        if not extra:
            extra = record.extra

        # Multiple value records need to be handled specially - we need to
        # pass values for other records as well
        multiple_value_record = record.extra.get('_multi_value', False)
        other_records = record.extra.get('_other_records', [])

        if multiple_value_record and other_records:
            self._update_multi_value_record(record=record, name=name,
                                            type=type, data=data,
                                            extra=extra)
        else:
            self._update_single_value_record(record=record, name=name,
                                             type=type, data=data,
                                             extra=extra)

        id = ':'.join((self.RECORD_TYPE_MAP[type], name))
        return Record(id=id, name=name, type=type, data=data, zone=record.zone,
                      driver=self, extra=extra)

    def delete_record(self, record):
        try:
            r = record
            batch = [('DELETE', r.name, r.type, r.data, r.extra)]
            self._post_changeset(record.zone, batch)
        except InvalidChangeBatch:
            raise RecordDoesNotExistError(value='', driver=self,
                                          record_id=r.id)
        return True

    def ex_create_multi_value_record(self, name, zone, type, data, extra=None):
        """
        Create a record with multiple values with a single call.

        :return: A list of created records.
        :rtype: ``list`` of :class:`libcloud.dns.base.Record`
        """
        extra = extra or {}

        attrs = {'xmlns': NAMESPACE}
        changeset = ET.Element('ChangeResourceRecordSetsRequest', attrs)
        batch = ET.SubElement(changeset, 'ChangeBatch')
        changes = ET.SubElement(batch, 'Changes')

        change = ET.SubElement(changes, 'Change')
        ET.SubElement(change, 'Action').text = 'CREATE'

        rrs = ET.SubElement(change, 'ResourceRecordSet')
        ET.SubElement(rrs, 'Name').text = name + '.' + zone.domain
        ET.SubElement(rrs, 'Type').text = self.RECORD_TYPE_MAP[type]
        ET.SubElement(rrs, 'TTL').text = str(extra.get('ttl', '0'))

        rrecs = ET.SubElement(rrs, 'ResourceRecords')

        # Value is provided as a multi line string
        values = [value.strip() for value in data.split('\n') if
                  value.strip()]

        for value in values:
            rrec = ET.SubElement(rrecs, 'ResourceRecord')
            ET.SubElement(rrec, 'Value').text = value

        uri = API_ROOT + 'hostedzone/' + zone.id + '/rrset'
        data = ET.tostring(changeset)
        self.connection.set_context({'zone_id': zone.id})
        self.connection.request(uri, method='POST', data=data)

        id = ':'.join((self.RECORD_TYPE_MAP[type], name))

        records = []
        for value in values:
            record = Record(id=id, name=name, type=type, data=value, zone=zone,
                            driver=self, extra=extra)
            records.append(record)

        return record

    def ex_delete_all_records(self, zone):
        """
        Remove all the records for the provided zone.

        :param zone: Zone to delete records for.
        :type  zone: :class:`Zone`
        """
        deletions = []
        for r in zone.list_records():
            if r.type in (RecordType.NS, RecordType.SOA):
                continue
            deletions.append(('DELETE', r.name, r.type, r.data, r.extra))

        if deletions:
            self._post_changeset(zone, deletions)

    def _update_single_value_record(self, record, name=None, type=None,
                                    data=None, extra=None):
        batch = [
            ('DELETE', record.name, record.type, record.data, record.extra),
            ('CREATE', name, type, data, extra)
        ]

        return self._post_changeset(record.zone, batch)

    def _update_multi_value_record(self, record, name=None, type=None,
                                   data=None, extra=None):
        other_records = record.extra.get('_other_records', [])

        attrs = {'xmlns': NAMESPACE}
        changeset = ET.Element('ChangeResourceRecordSetsRequest', attrs)
        batch = ET.SubElement(changeset, 'ChangeBatch')
        changes = ET.SubElement(batch, 'Changes')

        # Delete existing records
        change = ET.SubElement(changes, 'Change')
        ET.SubElement(change, 'Action').text = 'DELETE'

        rrs = ET.SubElement(change, 'ResourceRecordSet')
        ET.SubElement(rrs, 'Name').text = record.name + '.' + \
            record.zone.domain
        ET.SubElement(rrs, 'Type').text = self.RECORD_TYPE_MAP[record.type]
        ET.SubElement(rrs, 'TTL').text = str(record.extra.get('ttl', '0'))

        rrecs = ET.SubElement(rrs, 'ResourceRecords')

        rrec = ET.SubElement(rrecs, 'ResourceRecord')
        ET.SubElement(rrec, 'Value').text = record.data

        for other_record in other_records:
            rrec = ET.SubElement(rrecs, 'ResourceRecord')
            ET.SubElement(rrec, 'Value').text = other_record['data']

        # Re-create new (updated) records. Since we are updating a multi value
        # record, only a single record is updated and others are left as is.
        change = ET.SubElement(changes, 'Change')
        ET.SubElement(change, 'Action').text = 'CREATE'

        rrs = ET.SubElement(change, 'ResourceRecordSet')
        ET.SubElement(rrs, 'Name').text = name + '.' + record.zone.domain
        ET.SubElement(rrs, 'Type').text = self.RECORD_TYPE_MAP[type]
        ET.SubElement(rrs, 'TTL').text = str(extra.get('ttl', '0'))

        rrecs = ET.SubElement(rrs, 'ResourceRecords')

        rrec = ET.SubElement(rrecs, 'ResourceRecord')
        ET.SubElement(rrec, 'Value').text = data

        for other_record in other_records:
            rrec = ET.SubElement(rrecs, 'ResourceRecord')
            ET.SubElement(rrec, 'Value').text = other_record['data']

        uri = API_ROOT + 'hostedzone/' + record.zone.id + '/rrset'
        data = ET.tostring(changeset)
        self.connection.set_context({'zone_id': record.zone.id})
        response = self.connection.request(uri, method='POST', data=data)

        return response.status == httplib.OK

    def _post_changeset(self, zone, changes_list):
        attrs = {'xmlns': NAMESPACE}
        changeset = ET.Element('ChangeResourceRecordSetsRequest', attrs)
        batch = ET.SubElement(changeset, 'ChangeBatch')
        changes = ET.SubElement(batch, 'Changes')

        for action, name, type_, data, extra in changes_list:
            change = ET.SubElement(changes, 'Change')
            ET.SubElement(change, 'Action').text = action

            rrs = ET.SubElement(change, 'ResourceRecordSet')
            ET.SubElement(rrs, 'Name').text = name + '.' + zone.domain
            ET.SubElement(rrs, 'Type').text = self.RECORD_TYPE_MAP[type_]
            ET.SubElement(rrs, 'TTL').text = str(extra.get('ttl', '0'))

            rrecs = ET.SubElement(rrs, 'ResourceRecords')
            rrec = ET.SubElement(rrecs, 'ResourceRecord')
            ET.SubElement(rrec, 'Value').text = data

        uri = API_ROOT + 'hostedzone/' + zone.id + '/rrset'
        data = ET.tostring(changeset)
        self.connection.set_context({'zone_id': zone.id})
        response = self.connection.request(uri, method='POST', data=data)

        return response.status == httplib.OK

    def _to_zones(self, data):
        zones = []
        for element in data.findall(fixxpath(xpath='HostedZones/HostedZone',
                                             namespace=NAMESPACE)):
            zones.append(self._to_zone(element))

        return zones

    def _to_zone(self, elem):
        name = findtext(element=elem, xpath='Name', namespace=NAMESPACE)
        id = findtext(element=elem, xpath='Id',
                      namespace=NAMESPACE).replace('/hostedzone/', '')
        comment = findtext(element=elem, xpath='Config/Comment',
                           namespace=NAMESPACE)
        resource_record_count = int(findtext(element=elem,
                                             xpath='ResourceRecordSetCount',
                                             namespace=NAMESPACE))

        extra = {'Comment': comment, 'ResourceRecordSetCount':
                 resource_record_count}

        zone = Zone(id=id, domain=name, type='master', ttl=0, driver=self,
                    extra=extra)
        return zone

    def _to_records(self, data, zone):
        records = []
        elems = data.findall(
            fixxpath(xpath='ResourceRecordSets/ResourceRecordSet',
                     namespace=NAMESPACE))
        for elem in elems:
            record_set = elem.findall(fixxpath(
                                      xpath='ResourceRecords/ResourceRecord',
                                      namespace=NAMESPACE))
            record_count = len(record_set)
            multiple_value_record = (record_count > 1)

            record_set_records = []

            for index, record in enumerate(record_set):
                # Need to special handling for records with multiple values for
                # update to work correctly
                record = self._to_record(elem=elem, zone=zone, index=index)
                record.extra['_multi_value'] = multiple_value_record

                if multiple_value_record:
                    record.extra['_other_records'] = []

                record_set_records.append(record)

            # Store reference to other records so update works correctly
            if multiple_value_record:
                for index in range(0, len(record_set_records)):
                    record = record_set_records[index]

                    for other_index, other_record in \
                            enumerate(record_set_records):
                        if index == other_index:
                            # Skip current record
                            continue

                        extra = copy.deepcopy(other_record.extra)
                        extra.pop('_multi_value')
                        extra.pop('_other_records')

                        item = {'name': other_record.name,
                                'data': other_record.data,
                                'type': other_record.type,
                                'extra': extra}
                        record.extra['_other_records'].append(item)

            records.extend(record_set_records)

        return records

    def _to_record(self, elem, zone, index=0):
        name = findtext(element=elem, xpath='Name',
                        namespace=NAMESPACE)
        name = name[:-len(zone.domain) - 1]

        type = self._string_to_record_type(findtext(element=elem, xpath='Type',
                                                    namespace=NAMESPACE))
        ttl = int(findtext(element=elem, xpath='TTL', namespace=NAMESPACE))

        value_elem = elem.findall(
            fixxpath(xpath='ResourceRecords/ResourceRecord',
                     namespace=NAMESPACE))[index]
        data = findtext(element=(value_elem), xpath='Value',
                        namespace=NAMESPACE)

        extra = {'ttl': ttl}

        if type == 'MX':
            split = data.split()
            priority, data = split
            extra['priority'] = int(priority)
        elif type == 'SRV':
            split = data.split()
            priority, weight, port, data = split
            extra['priority'] = int(priority)
            extra['weight'] = int(weight)
            extra['port'] = int(port)

        id = ':'.join((self.RECORD_TYPE_MAP[type], name))
        record = Record(id=id, name=name, type=type, data=data, zone=zone,
                        driver=self, extra=extra)
        return record

    def _get_more(self, rtype, **kwargs):
        exhausted = False
        last_key = None
        while not exhausted:
            items, last_key, exhausted = self._get_data(rtype, last_key,
                                                        **kwargs)
            for item in items:
                yield item

    def _get_data(self, rtype, last_key, **kwargs):
        params = {}
        if last_key:
            params['name'] = last_key
        path = API_ROOT + 'hostedzone'

        if rtype == 'zones':
            response = self.connection.request(path, params=params)
            transform_func = self._to_zones
        elif rtype == 'records':
            zone = kwargs['zone']
            path += '/%s/rrset' % (zone.id)
            self.connection.set_context({'zone_id': zone.id})
            response = self.connection.request(path, params=params)
            transform_func = self._to_records

        if response.status == httplib.OK:
            is_truncated = findtext(element=response.object,
                                    xpath='IsTruncated',
                                    namespace=NAMESPACE)
            exhausted = is_truncated != 'true'
            last_key = findtext(element=response.object,
                                xpath='NextRecordName',
                                namespace=NAMESPACE)
            items = transform_func(data=response.object, **kwargs)
            return items, last_key, exhausted
        else:
            return [], None, True

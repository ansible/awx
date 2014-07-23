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

import datetime

from libcloud import __version__
from libcloud.common.base import ConnectionUserAndKey, BaseDriver
from libcloud.dns.types import RecordType

__all__ = [
    'Zone',
    'Record',
    'DNSDriver'
]


class Zone(object):
    """
    DNS zone.
    """

    def __init__(self, id, domain, type, ttl, driver, extra=None):
        """
        :param id: Zone id.
        :type id: ``str``

        :param domain: The name of the domain.
        :type domain: ``str``

        :param type: Zone type (master, slave).
        :type type: ``str``

        :param ttl: Default TTL for records in this zone (in seconds).
        :type ttl: ``int``

        :param driver: DNSDriver instance.
        :type driver: :class:`DNSDriver`

        :param extra: (optional) Extra attributes (driver specific).
        :type extra: ``dict``
        """
        self.id = str(id) if id else None
        self.domain = domain
        self.type = type
        self.ttl = ttl or None
        self.driver = driver
        self.extra = extra or {}

    def list_records(self):
        return self.driver.list_records(zone=self)

    def create_record(self, name, type, data, extra=None):
        return self.driver.create_record(name=name, zone=self, type=type,
                                         data=data, extra=extra)

    def update(self, domain=None, type=None, ttl=None, extra=None):
        return self.driver.update_zone(zone=self, domain=domain, type=type,
                                       ttl=ttl, extra=extra)

    def delete(self):
        return self.driver.delete_zone(zone=self)

    def export_to_bind_format(self):
        return self.driver.export_zone_to_bind_format(zone=self)

    def export_to_bind_zone_file(self, file_path):
        self.driver.export_zone_to_bind_zone_file(zone=self,
                                                  file_path=file_path)

    def __repr__(self):
        return ('<Zone: domain=%s, ttl=%s, provider=%s ...>' %
                (self.domain, self.ttl, self.driver.name))


class Record(object):
    """
    Zone record / resource.
    """

    def __init__(self, id, name, type, data, zone, driver, extra=None):
        """
        :param id: Record id
        :type id: ``str``

        :param name: Hostname or FQDN.
        :type name: ``str``

        :param type: DNS record type (A, AAAA, ...).
        :type type: :class:`RecordType`

        :param data: Data for the record (depends on the record type).
        :type data: ``str``

        :param zone: Zone instance.
        :type zone: :class:`Zone`

        :param driver: DNSDriver instance.
        :type driver: :class:`DNSDriver`

        :param extra: (optional) Extra attributes (driver specific).
        :type extra: ``dict``
        """
        self.id = str(id) if id else None
        self.name = name
        self.type = type
        self.data = data
        self.zone = zone
        self.driver = driver
        self.extra = extra or {}

    def update(self, name=None, type=None, data=None, extra=None):
        return self.driver.update_record(record=self, name=name, type=type,
                                         data=data, extra=extra)

    def delete(self):
        return self.driver.delete_record(record=self)

    def _get_numeric_id(self):
        record_id = self.id

        if record_id.isdigit():
            record_id = int(record_id)

        return record_id

    def __repr__(self):
        return ('<Record: zone=%s, name=%s, type=%s, data=%s, provider=%s '
                '...>' %
                (self.zone.id, self.name, self.type, self.data,
                 self.driver.name))


class DNSDriver(BaseDriver):
    """
    A base DNSDriver class to derive from

    This class is always subclassed by a specific driver.
    """
    connectionCls = ConnectionUserAndKey
    name = None
    website = None

    def __init__(self, key, secret=None, secure=True, host=None, port=None,
                 **kwargs):
        """
        :param    key: API key or username to used (required)
        :type     key: ``str``

        :param    secret: Secret password to be used (required)
        :type     secret: ``str``

        :param    secure: Weither to use HTTPS or HTTP. Note: Some providers
                only support HTTPS, and it is on by default.
        :type     secure: ``bool``

        :param    host: Override hostname used for connections.
        :type     host: ``str``

        :param    port: Override port used for connections.
        :type     port: ``int``

        :return: ``None``
        """
        super(DNSDriver, self).__init__(key=key, secret=secret, secure=secure,
                                        host=host, port=port, **kwargs)

    def list_record_types(self):
        """
        Return a list of RecordType objects supported by the provider.

        :return: ``list`` of :class:`RecordType`
        """
        return list(self.RECORD_TYPE_MAP.keys())

    def iterate_zones(self):
        """
        Return a generator to iterate over available zones.

        :rtype: ``generator`` of :class:`Zone`
        """
        raise NotImplementedError(
            'iterate_zones not implemented for this driver')

    def list_zones(self):
        """
        Return a list of zones.

        :return: ``list`` of :class:`Zone`
        """
        return list(self.iterate_zones())

    def iterate_records(self, zone):
        """
        Return a generator to iterate over records for the provided zone.

        :param zone: Zone to list records for.
        :type zone: :class:`Zone`

        :rtype: ``generator`` of :class:`Record`
        """
        raise NotImplementedError(
            'iterate_records not implemented for this driver')

    def list_records(self, zone):
        """
        Return a list of records for the provided zone.

        :param zone: Zone to list records for.
        :type zone: :class:`Zone`

        :return: ``list`` of :class:`Record`
        """
        return list(self.iterate_records(zone))

    def get_zone(self, zone_id):
        """
        Return a Zone instance.

        :param zone_id: ID of the required zone
        :type  zone_id: ``str``

        :rtype: :class:`Zone`
        """
        raise NotImplementedError(
            'get_zone not implemented for this driver')

    def get_record(self, zone_id, record_id):
        """
        Return a Record instance.

        :param zone_id: ID of the required zone
        :type  zone_id: ``str``

        :param record_id: ID of the required record
        :type  record_id: ``str``

        :rtype: :class:`Record`
        """
        raise NotImplementedError(
            'get_record not implemented for this driver')

    def create_zone(self, domain, type='master', ttl=None, extra=None):
        """
        Create a new zone.

        :param domain: Zone domain name (e.g. example.com)
        :type domain: ``str``

        :param type: Zone type (master / slave).
        :type  type: ``str``

        :param ttl: TTL for new records. (optional)
        :type  ttl: ``int``

        :param extra: Extra attributes (driver specific). (optional)
        :type extra: ``dict``

        :rtype: :class:`Zone`
        """
        raise NotImplementedError(
            'create_zone not implemented for this driver')

    def update_zone(self, zone, domain, type='master', ttl=None, extra=None):
        """
        Update en existing zone.

        :param zone: Zone to update.
        :type  zone: :class:`Zone`

        :param domain: Zone domain name (e.g. example.com)
        :type  domain: ``str``

        :param type: Zone type (master / slave).
        :type  type: ``str``

        :param ttl: TTL for new records. (optional)
        :type  ttl: ``int``

        :param extra: Extra attributes (driver specific). (optional)
        :type  extra: ``dict``

        :rtype: :class:`Zone`
        """
        raise NotImplementedError(
            'update_zone not implemented for this driver')

    def create_record(self, name, zone, type, data, extra=None):
        """
        Create a new record.

        :param name: Record name without the domain name (e.g. www).
                     Note: If you want to create a record for a base domain
                     name, you should specify empty string ('') for this
                     argument.
        :type  name: ``str``

        :param zone: Zone where the requested record is created.
        :type  zone: :class:`Zone`

        :param type: DNS record type (A, AAAA, ...).
        :type  type: :class:`RecordType`

        :param data: Data for the record (depends on the record type).
        :type  data: ``str``

        :param extra: Extra attributes (driver specific). (optional)
        :type extra: ``dict``

        :rtype: :class:`Record`
        """
        raise NotImplementedError(
            'create_record not implemented for this driver')

    def update_record(self, record, name, type, data, extra):
        """
        Update an existing record.

        :param record: Record to update.
        :type  record: :class:`Record`

        :param name: Record name without the domain name (e.g. www).
                     Note: If you want to create a record for a base domain
                     name, you should specify empty string ('') for this
                     argument.
        :type  name: ``str``

        :param type: DNS record type (A, AAAA, ...).
        :type  type: :class:`RecordType`

        :param data: Data for the record (depends on the record type).
        :type  data: ``str``

        :param extra: (optional) Extra attributes (driver specific).
        :type  extra: ``dict``

        :rtype: :class:`Record`
        """
        raise NotImplementedError(
            'update_record not implemented for this driver')

    def delete_zone(self, zone):
        """
        Delete a zone.

        Note: This will delete all the records belonging to this zone.

        :param zone: Zone to delete.
        :type  zone: :class:`Zone`

        :rtype: ``bool``
        """
        raise NotImplementedError(
            'delete_zone not implemented for this driver')

    def delete_record(self, record):
        """
        Delete a record.

        :param record: Record to delete.
        :type  record: :class:`Record`

        :rtype: ``bool``
        """
        raise NotImplementedError(
            'delete_record not implemented for this driver')

    def export_zone_to_bind_format(self, zone):
        """
        Export Zone object to the BIND compatible format.

        :param zone: Zone to export.
        :type  zone: :class:`Zone`

        :return: Zone data in BIND compatible format.
        :rtype: ``str``
        """
        if zone.type != 'master':
            raise ValueError('You can only generate BIND out for master zones')

        lines = []

        # For consistent output, records are sorted based on the id
        records = zone.list_records()
        records = sorted(records, key=Record._get_numeric_id)

        date = datetime.datetime.now().strftime('%Y-%m-%d %H:%m:%S')
        values = {'version': __version__, 'date': date}

        lines.append('; Generated by Libcloud v%(version)s on %(date)s' %
                     values)
        lines.append('$ORIGIN %(domain)s.' % {'domain': zone.domain})
        lines.append('$TTL %(domain_ttl)s\n' % {'domain_ttl': zone.ttl})

        for record in records:
            line = self._get_bind_record_line(record=record)
            lines.append(line)

        output = '\n'.join(lines)
        return output

    def export_zone_to_bind_zone_file(self, zone, file_path):
        """
        Export Zone object to the BIND compatible format and write result to a
        file.

        :param zone: Zone to export.
        :type  zone: :class:`Zone`

        :param file_path: File path where the output will be saved.
        :type  file_path: ``str``
        """
        result = self.export_zone_to_bind_format(zone=zone)

        with open(file_path, 'w') as fp:
            fp.write(result)

    def _get_bind_record_line(self, record):
        """
        Generate BIND record line for the provided record.

        :param record: Record to generate the line for.
        :type  record: :class:`Record`

        :return: Bind compatible record line.
        :rtype: ``str``
        """
        parts = []

        if record.name:
            name = '%(name)s.%(domain)s' % {'name': record.name,
                                            'domain': record.zone.domain}
        else:
            name = record.zone.domain

        name += '.'

        ttl = record.extra['ttl'] if 'ttl' in record.extra else record.zone.ttl
        ttl = str(ttl)
        data = record.data

        if record.type in [RecordType.CNAME, RecordType.DNAME, RecordType.MX,
                           RecordType.PTR, RecordType.SRV]:
            # Make sure trailing dot is present
            if data[len(data) - 1] != '.':
                data += '.'

        if record.type in [RecordType.TXT, RecordType.SPF] and ' ' in data:
            # Escape the quotes
            data = data.replace('"', '\\"')

            # Quote the string
            data = '"%s"' % (data)

        if record.type in [RecordType.MX, RecordType.SRV]:
            priority = str(record.extra['priority'])
            parts = [name, ttl, 'IN', record.type, priority, data]
        else:
            parts = [name, ttl, 'IN', record.type, data]

        line = '\t'.join(parts)
        return line

    def _string_to_record_type(self, string):
        """
        Return a string representation of a DNS record type to a
        libcloud RecordType ENUM.

        :rtype: ``str``
        """
        string = string.upper()
        record_type = getattr(RecordType, string)
        return record_type

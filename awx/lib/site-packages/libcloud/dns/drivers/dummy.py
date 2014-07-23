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

from libcloud.dns.base import DNSDriver, Zone, Record
from libcloud.dns.types import RecordType
from libcloud.dns.types import ZoneDoesNotExistError, ZoneAlreadyExistsError
from libcloud.dns.types import RecordDoesNotExistError
from libcloud.dns.types import RecordAlreadyExistsError


class DummyDNSDriver(DNSDriver):
    """
    Dummy DNS driver.

    >>> from libcloud.dns.drivers.dummy import DummyDNSDriver
    >>> driver = DummyDNSDriver('key', 'secret')
    >>> driver.name
    'Dummy DNS Provider'
    """

    name = 'Dummy DNS Provider'
    website = 'http://example.com'

    def __init__(self, api_key, api_secret):
        """
        :param    api_key:    API key or username to used (required)
        :type     api_key:    ``str``

        :param    api_secret: Secret password to be used (required)
        :type     api_secret: ``str``

        :rtype: ``None``
        """
        self._zones = {}

    def list_record_types(self):
        """
        >>> driver = DummyDNSDriver('key', 'secret')
        >>> driver.list_record_types()
        ['A']

        @inherits: :class:`DNSDriver.list_record_types`
        """
        return [RecordType.A]

    def list_zones(self):
        """
        >>> driver = DummyDNSDriver('key', 'secret')
        >>> driver.list_zones()
        []

        @inherits: :class:`DNSDriver.list_zones`
        """

        return [zone['zone'] for zone in list(self._zones.values())]

    def list_records(self, zone):
        """
        >>> driver = DummyDNSDriver('key', 'secret')
        >>> zone = driver.create_zone(domain='apache.org', type='master',
        ...                           ttl=100)
        >>> list(zone.list_records())
        []
        >>> record = driver.create_record(name='libcloud', zone=zone,
        ...                               type=RecordType.A, data='127.0.0.1')
        >>> list(zone.list_records()) #doctest: +ELLIPSIS
        [<Record: zone=id-apache.org, name=libcloud, type=A...>]
        """
        return self._zones[zone.id]['records'].values()

    def get_zone(self, zone_id):
        """
        >>> driver = DummyDNSDriver('key', 'secret')
        >>> driver.get_zone(zone_id='foobar')
        ... #doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ZoneDoesNotExistError:

        @inherits: :class:`DNSDriver.get_zone`
        """

        if zone_id not in self._zones:
            raise ZoneDoesNotExistError(driver=self, value=None,
                                        zone_id=zone_id)

        return self._zones[zone_id]['zone']

    def get_record(self, zone_id, record_id):
        """
        >>> driver = DummyDNSDriver('key', 'secret')
        >>> driver.get_record(zone_id='doesnotexist', record_id='exists')
        ... #doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ZoneDoesNotExistError:

        @inherits: :class:`DNSDriver.get_record`
        """

        self.get_zone(zone_id=zone_id)
        zone_records = self._zones[zone_id]['records']

        if record_id not in zone_records:
            raise RecordDoesNotExistError(record_id=record_id, value=None,
                                          driver=self)

        return zone_records[record_id]

    def create_zone(self, domain, type='master', ttl=None, extra=None):
        """
        >>> driver = DummyDNSDriver('key', 'secret')
        >>> zone = driver.create_zone(domain='apache.org', type='master',
        ...                           ttl=100)
        >>> zone
        <Zone: domain=apache.org, ttl=100, provider=Dummy DNS Provider ...>
        >>> zone = driver.create_zone(domain='apache.org', type='master',
        ...                           ttl=100)
        ... #doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ZoneAlreadyExistsError:

        @inherits: :class:`DNSDriver.create_zone`
        """

        id = 'id-%s' % (domain)

        if id in self._zones:
            raise ZoneAlreadyExistsError(zone_id=id, value=None, driver=self)

        zone = Zone(id=id, domain=domain, type=type, ttl=ttl, extra={},
                    driver=self)
        self._zones[id] = {'zone': zone,
                           'records': {}}
        return zone

    def create_record(self, name, zone, type, data, extra=None):
        """
        >>> driver = DummyDNSDriver('key', 'secret')
        >>> zone = driver.create_zone(domain='apache.org', type='master',
        ...                           ttl=100)
        >>> record = driver.create_record(name='libcloud', zone=zone,
        ...                               type=RecordType.A, data='127.0.0.1')
        >>> record #doctest: +ELLIPSIS
        <Record: zone=id-apache.org, name=libcloud, type=A, data=127.0.0.1...>
        >>> record = driver.create_record(name='libcloud', zone=zone,
        ...                               type=RecordType.A, data='127.0.0.1')
        ... #doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        RecordAlreadyExistsError:

        @inherits: :class:`DNSDriver.create_record`
        """
        id = 'id-%s' % (name)

        zone = self.get_zone(zone_id=zone.id)

        if id in self._zones[zone.id]['records']:
            raise RecordAlreadyExistsError(record_id=id, value=None,
                                           driver=self)

        record = Record(id=id, name=name, type=type, data=data, extra=extra,
                        zone=zone, driver=self)
        self._zones[zone.id]['records'][id] = record
        return record

    def delete_zone(self, zone):
        """
        >>> driver = DummyDNSDriver('key', 'secret')
        >>> zone = driver.create_zone(domain='apache.org', type='master',
        ...                           ttl=100)
        >>> driver.delete_zone(zone)
        True
        >>> driver.delete_zone(zone) #doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ZoneDoesNotExistError:

        @inherits: :class:`DNSDriver.delete_zone`
        """
        self.get_zone(zone_id=zone.id)

        del self._zones[zone.id]
        return True

    def delete_record(self, record):
        """
        >>> driver = DummyDNSDriver('key', 'secret')
        >>> zone = driver.create_zone(domain='apache.org', type='master',
        ...                           ttl=100)
        >>> record = driver.create_record(name='libcloud', zone=zone,
        ...                               type=RecordType.A, data='127.0.0.1')
        >>> driver.delete_record(record)
        True
        >>> driver.delete_record(record) #doctest: +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        RecordDoesNotExistError:

        @inherits: :class:`DNSDriver.delete_record`
        """
        self.get_record(zone_id=record.zone.id, record_id=record.id)

        del self._zones[record.zone.id]['records'][record.id]
        return True


if __name__ == "__main__":
    import doctest
    doctest.testmod()

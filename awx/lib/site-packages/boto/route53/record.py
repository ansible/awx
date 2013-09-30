# Copyright (c) 2010 Chris Moyer http://coredumped.org/
# Copyright (c) 2012 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2012 Amazon.com, Inc. or its affiliates.
# All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

RECORD_TYPES = ['A', 'AAAA', 'TXT', 'CNAME', 'MX', 'PTR', 'SRV', 'SPF']

from boto.resultset import ResultSet
class ResourceRecordSets(ResultSet):
    """
    A list of resource records.

    :ivar hosted_zone_id: The ID of the hosted zone.
    :ivar comment: A comment that will be stored with the change.
    :ivar changes: A list of changes.
    """

    ChangeResourceRecordSetsBody = """<?xml version="1.0" encoding="UTF-8"?>
    <ChangeResourceRecordSetsRequest xmlns="https://route53.amazonaws.com/doc/2012-02-29/">
            <ChangeBatch>
                <Comment>%(comment)s</Comment>
                <Changes>%(changes)s</Changes>
            </ChangeBatch>
        </ChangeResourceRecordSetsRequest>"""

    ChangeXML = """<Change>
        <Action>%(action)s</Action>
        %(record)s
    </Change>"""

    def __init__(self, connection=None, hosted_zone_id=None, comment=None):
        self.connection = connection
        self.hosted_zone_id = hosted_zone_id
        self.comment = comment
        self.changes = []
        self.next_record_name = None
        self.next_record_type = None
        ResultSet.__init__(self, [('ResourceRecordSet', Record)])

    def __repr__(self):
        if self.changes:
            record_list = ','.join([c.__repr__() for c in self.changes])
        else:
            record_list = ','.join([record.__repr__() for record in self])
        return '<ResourceRecordSets:%s [%s]' % (self.hosted_zone_id,
                                                record_list)

    def add_change(self, action, name, type, ttl=600,
            alias_hosted_zone_id=None, alias_dns_name=None, identifier=None,
            weight=None, region=None):
        """
        Add a change request to the set.

        :type action: str
        :param action: The action to perform ('CREATE'|'DELETE')

        :type name: str
        :param name: The name of the domain you want to perform the action on.

        :type type: str
        :param type: The DNS record type.  Valid values are:

            * A
            * AAAA
            * CNAME
            * MX
            * NS
            * PTR
            * SOA
            * SPF
            * SRV
            * TXT

        :type ttl: int
        :param ttl: The resource record cache time to live (TTL), in seconds.

        :type alias_hosted_zone_id: str
        :param alias_dns_name: *Alias resource record sets only* The value
            of the hosted zone ID, CanonicalHostedZoneNameId, for
            the LoadBalancer.

        :type alias_dns_name: str
        :param alias_hosted_zone_id: *Alias resource record sets only*
            Information about the domain to which you are redirecting traffic.

        :type identifier: str
        :param identifier: *Weighted and latency-based resource record sets
            only* An identifier that differentiates among multiple resource
            record sets that have the same combination of DNS name and type.

        :type weight: int
        :param weight: *Weighted resource record sets only* Among resource
            record sets that have the same combination of DNS name and type,
            a value that determines what portion of traffic for the current
            resource record set is routed to the associated location

        :type region: str
        :param region: *Latency-based resource record sets only* Among resource
            record sets that have the same combination of DNS name and type,
            a value that determines which region this should be associated with
            for the latency-based routing
        """
        change = Record(name, type, ttl,
                alias_hosted_zone_id=alias_hosted_zone_id,
                alias_dns_name=alias_dns_name, identifier=identifier,
                weight=weight, region=region)
        self.changes.append([action, change])
        return change

    def add_change_record(self, action, change):
        """Add an existing record to a change set with the specified action"""
        self.changes.append([action, change])
        return

    def to_xml(self):
        """Convert this ResourceRecordSet into XML
        to be saved via the ChangeResourceRecordSetsRequest"""
        changesXML = ""
        for change in self.changes:
            changeParams = {"action": change[0], "record": change[1].to_xml()}
            changesXML += self.ChangeXML % changeParams
        params = {"comment": self.comment, "changes": changesXML}
        return self.ChangeResourceRecordSetsBody % params

    def commit(self):
        """Commit this change"""
        if not self.connection:
            import boto
            self.connection = boto.connect_route53()
        return self.connection.change_rrsets(self.hosted_zone_id, self.to_xml())

    def endElement(self, name, value, connection):
        """Overwritten to also add the NextRecordName and
        NextRecordType to the base object"""
        if name == 'NextRecordName':
            self.next_record_name = value
        elif name == 'NextRecordType':
            self.next_record_type = value
        else:
            return ResultSet.endElement(self, name, value, connection)

    def __iter__(self):
        """Override the next function to support paging"""
        results = ResultSet.__iter__(self)
        truncated = self.is_truncated
        while results:
            for obj in results:
                yield obj
            if self.is_truncated:
                self.is_truncated = False
                results = self.connection.get_all_rrsets(self.hosted_zone_id, name=self.next_record_name, type=self.next_record_type)
            else:
                results = None
                self.is_truncated = truncated




class Record(object):
    """An individual ResourceRecordSet"""

    XMLBody = """<ResourceRecordSet>
        <Name>%(name)s</Name>
        <Type>%(type)s</Type>
        %(weight)s
        %(body)s
    </ResourceRecordSet>"""

    WRRBody = """
        <SetIdentifier>%(identifier)s</SetIdentifier>
        <Weight>%(weight)s</Weight>
    """

    RRRBody = """
        <SetIdentifier>%(identifier)s</SetIdentifier>
        <Region>%(region)s</Region>
    """

    ResourceRecordsBody = """
        <TTL>%(ttl)s</TTL>
        <ResourceRecords>
            %(records)s
        </ResourceRecords>"""

    ResourceRecordBody = """<ResourceRecord>
        <Value>%s</Value>
    </ResourceRecord>"""

    AliasBody = """<AliasTarget>
        <HostedZoneId>%s</HostedZoneId>
        <DNSName>%s</DNSName>
    </AliasTarget>"""



    def __init__(self, name=None, type=None, ttl=600, resource_records=None,
            alias_hosted_zone_id=None, alias_dns_name=None, identifier=None,
            weight=None, region=None):
        self.name = name
        self.type = type
        self.ttl = ttl
        if resource_records == None:
            resource_records = []
        self.resource_records = resource_records
        self.alias_hosted_zone_id = alias_hosted_zone_id
        self.alias_dns_name = alias_dns_name
        self.identifier = identifier
        self.weight = weight
        self.region = region

    def __repr__(self):
        return '<Record:%s:%s:%s>' % (self.name, self.type, self.to_print())

    def add_value(self, value):
        """Add a resource record value"""
        self.resource_records.append(value)

    def set_alias(self, alias_hosted_zone_id, alias_dns_name):
        """Make this an alias resource record set"""
        self.alias_hosted_zone_id = alias_hosted_zone_id
        self.alias_dns_name = alias_dns_name

    def to_xml(self):
        """Spit this resource record set out as XML"""
        if self.alias_hosted_zone_id != None and self.alias_dns_name != None:
            # Use alias
            body = self.AliasBody % (self.alias_hosted_zone_id, self.alias_dns_name)
        else:
            # Use resource record(s)
            records = ""

            for r in self.resource_records:
                records += self.ResourceRecordBody % r

            body = self.ResourceRecordsBody % {
                "ttl": self.ttl,
                "records": records,
            }

        weight = ""

        if self.identifier != None and self.weight != None:
            weight = self.WRRBody % {"identifier": self.identifier, "weight":
                    self.weight}
        elif self.identifier != None and self.region != None:
            weight = self.RRRBody % {"identifier": self.identifier, "region":
                    self.region}

        params = {
            "name": self.name,
            "type": self.type,
            "weight": weight,
            "body": body,
        }
        return self.XMLBody % params

    def to_print(self):
        rr = ""
        if self.alias_hosted_zone_id != None and self.alias_dns_name != None:
            # Show alias
            rr = 'ALIAS ' + self.alias_hosted_zone_id + ' ' + self.alias_dns_name
        else:
            # Show resource record(s)
            rr =  ",".join(self.resource_records)

        if self.identifier != None and self.weight != None:
            rr += ' (WRR id=%s, w=%s)' % (self.identifier, self.weight)
        elif self.identifier != None and self.region != None:
            rr += ' (LBR id=%s, region=%s)' % (self.identifier, self.region)

        return rr

    def endElement(self, name, value, connection):
        if name == 'Name':
            self.name = value
        elif name == 'Type':
            self.type = value
        elif name == 'TTL':
            self.ttl = value
        elif name == 'Value':
            self.resource_records.append(value)
        elif name == 'HostedZoneId':
            self.alias_hosted_zone_id = value
        elif name == 'DNSName':
            self.alias_dns_name = value
        elif name == 'SetIdentifier':
            self.identifier = value
        elif name == 'Weight':
            self.weight = value
        elif name == 'Region':
            self.region = value

    def startElement(self, name, attrs, connection):
        return None

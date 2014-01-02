# Copyright (c) 2009-2010 Mitch Garnaat http://garnaat.org/
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

"""
Represents a Virtual Private Cloud.
"""

from boto.ec2.ec2object import TaggedEC2Object

class VPC(TaggedEC2Object):

    def __init__(self, connection=None):
        """
        Represents a VPC.

        :ivar id: The unique ID of the VPC.
        :ivar dhcp_options_id: The ID of the set of DHCP options you've associated with the VPC
                                (or default if the default options are associated with the VPC).
        :ivar state: The current state of the VPC.
        :ivar cidr_block: The CIDR block for the VPC.
        :ivar is_default: Indicates whether the VPC is the default VPC.
        :ivar instance_tenancy: The allowed tenancy of instances launched into the VPC.
        """
        super(VPC, self).__init__(connection)
        self.id = None
        self.dhcp_options_id = None
        self.state = None
        self.cidr_block = None
        self.is_default = None
        self.instance_tenancy = None

    def __repr__(self):
        return 'VPC:%s' % self.id

    def endElement(self, name, value, connection):
        if name == 'vpcId':
            self.id = value
        elif name == 'dhcpOptionsId':
            self.dhcp_options_id = value
        elif name == 'state':
            self.state = value
        elif name == 'cidrBlock':
            self.cidr_block = value
        elif name == 'isDefault':
            self.is_default = True if value == 'true' else False
        elif name == 'instanceTenancy':
            self.instance_tenancy = value
        else:
            setattr(self, name, value)

    def delete(self):
        return self.connection.delete_vpc(self.id)

    def _update(self, updated):
        self.__dict__.update(updated.__dict__)

    def update(self, validate=False, dry_run=False):
        vpc_list = self.connection.get_all_vpcs(
            [self.id],
            dry_run=dry_run
        )
        if len(vpc_list):
            updated_vpc = vpc_list[0]
            self._update(updated_vpc)
        elif validate:
            raise ValueError('%s is not a valid VPC ID' % (self.id,))
        return self.state

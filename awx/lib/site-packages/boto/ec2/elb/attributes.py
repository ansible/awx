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
#
# Created by Chris Huegle for TellApart, Inc.

class CrossZoneLoadBalancingAttribute(object):
    """
    Represents the CrossZoneLoadBalancing segement of ELB Attributes.
    """
    def __init__(self, connection=None):
        self.enabled = None

    def __repr__(self):
        return 'CrossZoneLoadBalancingAttribute(%s)' % (
            self.enabled)

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'Enabled':
            if value.lower() == 'true':
                self.enabled = True
            else:
                self.enabled = False

class LbAttributes(object):
    """
    Represents the Attributes of an Elastic Load Balancer.
    """
    def __init__(self, connection=None):
        self.connection = connection
        self.cross_zone_load_balancing = CrossZoneLoadBalancingAttribute(
          self.connection)

    def __repr__(self):
        return 'LbAttributes(%s)' % (
            repr(self.cross_zone_load_balancing))

    def startElement(self, name, attrs, connection):
        if name == 'CrossZoneLoadBalancing':
            return self.cross_zone_load_balancing
        
    def endElement(self, name, value, connection):
        pass

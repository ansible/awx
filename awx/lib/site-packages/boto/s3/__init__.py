# Copyright (c) 2006-2012 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2010, Eucalyptus Systems, Inc.
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
#

from boto.regioninfo import RegionInfo


class S3RegionInfo(RegionInfo):

    def connect(self, **kw_params):
        """
        Connect to this Region's endpoint. Returns an connection
        object pointing to the endpoint associated with this region.
        You may pass any of the arguments accepted by the connection
        class's constructor as keyword arguments and they will be
        passed along to the connection object.

        :rtype: Connection object
        :return: The connection to this regions endpoint
        """
        if self.connection_cls:
            return self.connection_cls(host=self.endpoint, **kw_params)


def regions():
    """
    Get all available regions for the Amazon S3 service.

    :rtype: list
    :return: A list of :class:`boto.regioninfo.RegionInfo`
    """
    from .connection import S3Connection
    return [S3RegionInfo(name='us-east-1',
                         endpoint='s3.amazonaws.com',
                         connection_cls=S3Connection),
            S3RegionInfo(name='us-gov-west-1',
                         endpoint='s3-us-gov-west-1.amazonaws.com',
                       connection_cls=S3Connection),
            S3RegionInfo(name='us-west-1',
                         endpoint='s3-us-west-1.amazonaws.com',
                       connection_cls=S3Connection),
            S3RegionInfo(name='us-west-2',
                         endpoint='s3-us-west-2.amazonaws.com',
                         connection_cls=S3Connection),
            S3RegionInfo(name='ap-northeast-1',
                         endpoint='s3-ap-northeast-1.amazonaws.com',
                         connection_cls=S3Connection),
            S3RegionInfo(name='ap-southeast-1',
                         endpoint='s3-ap-southeast-1.amazonaws.com',
                         connection_cls=S3Connection),
            S3RegionInfo(name='ap-southeast-2',
                         endpoint='s3-ap-southeast-2.amazonaws.com',
                         connection_cls=S3Connection),
            S3RegionInfo(name='eu-west-1',
                         endpoint='s3-eu-west-1.amazonaws.com',
                         connection_cls=S3Connection),
            S3RegionInfo(name='sa-east-1',
                         endpoint='s3-sa-east-1.amazonaws.com',
                         connection_cls=S3Connection),
            ]


def connect_to_region(region_name, **kw_params):
    for region in regions():
        if region.name == region_name:
            return region.connect(**kw_params)
    return None

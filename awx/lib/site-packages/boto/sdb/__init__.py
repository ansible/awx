# Copyright (c) 2006-2009 Mitch Garnaat http://garnaat.org/
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

from .regioninfo import SDBRegionInfo


def regions():
    """
    Get all available regions for the SDB service.

    :rtype: list
    :return: A list of :class:`boto.sdb.regioninfo.RegionInfo` instances
    """
    return [SDBRegionInfo(name='us-east-1',
                          endpoint='sdb.amazonaws.com'),
            SDBRegionInfo(name='eu-west-1',
                          endpoint='sdb.eu-west-1.amazonaws.com'),
            SDBRegionInfo(name='us-west-1',
                          endpoint='sdb.us-west-1.amazonaws.com'),
            SDBRegionInfo(name='sa-east-1',
                          endpoint='sdb.sa-east-1.amazonaws.com'),
            SDBRegionInfo(name='us-west-2',
                          endpoint='sdb.us-west-2.amazonaws.com'),
            SDBRegionInfo(name='ap-northeast-1',
                          endpoint='sdb.ap-northeast-1.amazonaws.com'),
            SDBRegionInfo(name='ap-southeast-1',
                          endpoint='sdb.ap-southeast-1.amazonaws.com'),
            SDBRegionInfo(name='ap-southeast-2',
                          endpoint='sdb.ap-southeast-2.amazonaws.com')
            ]


def connect_to_region(region_name, **kw_params):
    """
    Given a valid region name, return a
    :class:`boto.sdb.connection.SDBConnection`.

    :type: str
    :param region_name: The name of the region to connect to.

    :rtype: :class:`boto.sdb.connection.SDBConnection` or ``None``
    :return: A connection to the given region, or None if an invalid region
             name is given
    """
    for region in regions():
        if region.name == region_name:
            return region.connect(**kw_params)
    return None

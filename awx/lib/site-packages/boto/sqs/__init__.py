# Copyright (c) 2006-2012 Mitch Garnaat http://garnaat.org/
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

from regioninfo import SQSRegionInfo


def regions():
    """
    Get all available regions for the SQS service.

    :rtype: list
    :return: A list of :class:`boto.sqs.regioninfo.RegionInfo`
    """
    return [SQSRegionInfo(name='us-east-1',
                          endpoint='queue.amazonaws.com'),
            SQSRegionInfo(name='us-gov-west-1',
                          endpoint='sqs.us-gov-west-1.amazonaws.com'),
            SQSRegionInfo(name='eu-west-1',
                          endpoint='eu-west-1.queue.amazonaws.com'),
            SQSRegionInfo(name='us-west-1',
                          endpoint='us-west-1.queue.amazonaws.com'),
            SQSRegionInfo(name='us-west-2',
                          endpoint='us-west-2.queue.amazonaws.com'),
            SQSRegionInfo(name='sa-east-1',
                          endpoint='sa-east-1.queue.amazonaws.com'),
            SQSRegionInfo(name='ap-northeast-1',
                          endpoint='ap-northeast-1.queue.amazonaws.com'),
            SQSRegionInfo(name='ap-southeast-1',
                          endpoint='ap-southeast-1.queue.amazonaws.com'),
            SQSRegionInfo(name='ap-southeast-2',
                          endpoint='ap-southeast-2.queue.amazonaws.com')
            ]


def connect_to_region(region_name, **kw_params):
    for region in regions():
        if region.name == region_name:
            return region.connect(**kw_params)
    return None

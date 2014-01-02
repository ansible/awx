# Copyright (c) 2012 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2012 Amazon.com, Inc. or its affiliates.
# All Rights Reserved
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

from boto.ec2.regioninfo import RegionInfo
import boto.swf.layer1

REGION_ENDPOINTS = {
    'us-east-1': 'swf.us-east-1.amazonaws.com',
    'us-gov-west-1': 'swf.us-gov-west-1.amazonaws.com',
    'us-west-1': 'swf.us-west-1.amazonaws.com',
    'us-west-2': 'swf.us-west-2.amazonaws.com',
    'sa-east-1': 'swf.sa-east-1.amazonaws.com',
    'eu-west-1': 'swf.eu-west-1.amazonaws.com',
    'ap-northeast-1': 'swf.ap-northeast-1.amazonaws.com',
    'ap-southeast-1': 'swf.ap-southeast-1.amazonaws.com',
    'ap-southeast-2': 'swf.ap-southeast-2.amazonaws.com',
    'cn-north-1': 'swf.cn-north-1.amazonaws.com.cn',
}


def regions(**kw_params):
    """
    Get all available regions for the Amazon Simple Workflow service.

    :rtype: list
    :return: A list of :class:`boto.regioninfo.RegionInfo`
    """
    return [RegionInfo(name=region_name, endpoint=REGION_ENDPOINTS[region_name],
                       connection_cls=boto.swf.layer1.Layer1)
            for region_name in REGION_ENDPOINTS]


def connect_to_region(region_name, **kw_params):
    for region in regions():
        if region.name == region_name:
            return region.connect(**kw_params)
    return None

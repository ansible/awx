# Copyright (c) 2011 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2011 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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


def regions():
    """
    Get all available regions for the Amazon DynamoDB service.

    :rtype: list
    :return: A list of :class:`boto.regioninfo.RegionInfo`
    """
    from boto.dynamodb2.layer1 import DynamoDBConnection
    return [RegionInfo(name='us-east-1',
                       endpoint='dynamodb.us-east-1.amazonaws.com',
                       connection_cls=DynamoDBConnection),
            RegionInfo(name='us-gov-west-1',
                       endpoint='dynamodb.us-gov-west-1.amazonaws.com',
                       connection_cls=DynamoDBConnection),
            RegionInfo(name='us-west-1',
                       endpoint='dynamodb.us-west-1.amazonaws.com',
                       connection_cls=DynamoDBConnection),
            RegionInfo(name='us-west-2',
                       endpoint='dynamodb.us-west-2.amazonaws.com',
                       connection_cls=DynamoDBConnection),
            RegionInfo(name='eu-west-1',
                       endpoint='dynamodb.eu-west-1.amazonaws.com',
                       connection_cls=DynamoDBConnection),
            RegionInfo(name='ap-northeast-1',
                       endpoint='dynamodb.ap-northeast-1.amazonaws.com',
                       connection_cls=DynamoDBConnection),
            RegionInfo(name='ap-southeast-1',
                       endpoint='dynamodb.ap-southeast-1.amazonaws.com',
                       connection_cls=DynamoDBConnection),
            RegionInfo(name='ap-southeast-2',
                       endpoint='dynamodb.ap-southeast-2.amazonaws.com',
                       connection_cls=DynamoDBConnection),
            RegionInfo(name='sa-east-1',
                       endpoint='dynamodb.sa-east-1.amazonaws.com',
                       connection_cls=DynamoDBConnection),
            RegionInfo(name='cn-north-1',
                       endpoint='dynamodb.cn-north-1.amazonaws.com.cn',
                       connection_cls=DynamoDBConnection),
            ]


def connect_to_region(region_name, **kw_params):
    for region in regions():
        if region.name == region_name:
            return region.connect(**kw_params)
    return None

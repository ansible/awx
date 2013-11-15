# Copyright (c) 2013 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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

try:
    import json
except ImportError:
    import simplejson as json

import boto
from boto.connection import AWSQueryConnection
from boto.regioninfo import RegionInfo
from boto.exception import JSONResponseError
from boto.cloudtrail import exceptions


class CloudTrailConnection(AWSQueryConnection):
    """
    AWS Cloud Trail
    This is the CloudTrail API Reference. It provides descriptions of
    actions, data types, common parameters, and common errors for
    CloudTrail.

    CloudTrail is a web service that records AWS API calls for your
    AWS account and delivers log files to an Amazon S3 bucket. The
    recorded information includes the identity of the user, the start
    time of the event, the source IP address, the request parameters,
    and the response elements returned by the service.

    As an alternative to using the API, you can use one of the AWS
    SDKs, which consist of libraries and sample code for various
    programming languages and platforms (Java, Ruby, .NET, iOS,
    Android, etc.). The SDKs provide a convenient way to create
    programmatic access to AWSCloudTrail. For example, the SDKs take
    care of cryptographically signing requests, managing errors, and
    retrying requests automatically. For information about the AWS
    SDKs, including how to download and install them, see the Tools
    for Amazon Web Services page.

    See the CloudTrail User Guide for information about the data that
    is included with each event listed in the log files.
    """
    APIVersion = "2013-11-01"
    DefaultRegionName = "us-east-1"
    DefaultRegionEndpoint = "cloudtrail.us-east-1.amazonaws.com"
    ServiceName = "CloudTrail"
    TargetPrefix = "com.amazonaws.cloudtrail.v20131101.CloudTrail_20131101"
    ResponseError = JSONResponseError

    _faults = {
        "InvalidSnsTopicNameException": exceptions.InvalidSnsTopicNameException,
        "InvalidS3BucketNameException": exceptions.InvalidS3BucketNameException,
        "TrailAlreadyExistsException": exceptions.TrailAlreadyExistsException,
        "InsufficientSnsTopicPolicyException": exceptions.InsufficientSnsTopicPolicyException,
        "InvalidTrailNameException": exceptions.InvalidTrailNameException,
        "InternalErrorException": exceptions.InternalErrorException,
        "TrailNotFoundException": exceptions.TrailNotFoundException,
        "S3BucketDoesNotExistException": exceptions.S3BucketDoesNotExistException,
        "TrailNotProvidedException": exceptions.TrailNotProvidedException,
        "InvalidS3PrefixException": exceptions.InvalidS3PrefixException,
        "MaximumNumberOfTrailsExceededException": exceptions.MaximumNumberOfTrailsExceededException,
        "InsufficientS3BucketPolicyException": exceptions.InsufficientS3BucketPolicyException,
    }


    def __init__(self, **kwargs):
        region = kwargs.pop('region', None)
        if not region:
            region = RegionInfo(self, self.DefaultRegionName,
                                self.DefaultRegionEndpoint)

        if 'host' not in kwargs:
            kwargs['host'] = region.endpoint

        AWSQueryConnection.__init__(self, **kwargs)
        self.region = region

    def _required_auth_capability(self):
        return ['hmac-v4']

    def create_trail(self, trail=None):
        """
        From the command line, use create-subscription.

        Creates a trail that specifies the settings for delivery of
        log data to an Amazon S3 bucket. The request includes a Trail
        structure that specifies the following:


        + Trail name.
        + The name of the Amazon S3 bucket to which CloudTrail
          delivers your log files.
        + The name of the Amazon S3 key prefix that precedes each log
          file.
        + The name of the Amazon SNS topic that notifies you that a
          new file is available in your bucket.
        + Whether the log file should include events from global
          services. Currently, the only events included in CloudTrail
          log files are from IAM and AWS STS.


        Returns the appropriate HTTP status code if successful. If
        not, it returns either one of the CommonErrors or a
        FrontEndException with one of the following error codes:

        **MaximumNumberOfTrailsExceeded**

        An attempt was made to create more trails than allowed. You
        can only create one trail for each account in each region.

        **TrailAlreadyExists**

        At attempt was made to create a trail with a name that already
        exists.

        **S3BucketDoesNotExist**

        Specified Amazon S3 bucket does not exist.

        **InsufficientS3BucketPolicy**

        Policy on Amazon S3 bucket does not permit CloudTrail to write
        to your bucket. See the AWS AWS CloudTrail User Guide for the
        required bucket policy.

        **InsufficientSnsTopicPolicy**

        The policy on Amazon SNS topic does not permit CloudTrail to
        write to it. Can also occur when an Amazon SNS topic does not
        exist.

        :type trail: dict
        :param trail: Contains the Trail structure that specifies the settings
            for each trail.

        """
        params = {}
        if trail is not None:
            params['trail'] = trail
        return self.make_request(action='CreateTrail',
                                 body=json.dumps(params))

    def delete_trail(self, name=None):
        """
        Deletes a trail.

        :type name: string
        :param name: The name of a trail to be deleted.

        """
        params = {}
        if name is not None:
            params['Name'] = name
        return self.make_request(action='DeleteTrail',
                                 body=json.dumps(params))

    def describe_trails(self, trail_name_list=None):
        """
        Retrieves the settings for some or all trails associated with
        an account. Returns a list of Trail structures in JSON format.

        :type trail_name_list: list
        :param trail_name_list: The list of Trail object names.

        """
        params = {}
        if trail_name_list is not None:
            params['trailNameList'] = trail_name_list
        return self.make_request(action='DescribeTrails',
                                 body=json.dumps(params))

    def get_trail_status(self, name=None):
        """
        Returns GetTrailStatusResult, which contains a JSON-formatted
        list of information about the trail specified in the request.
        JSON fields include information such as delivery errors,
        Amazon SNS and Amazon S3 errors, and times that logging
        started and stopped for each trail.

        :type name: string
        :param name: The name of the trail for which you are requesting the
            current status.

        """
        params = {}
        if name is not None:
            params['Name'] = name
        return self.make_request(action='GetTrailStatus',
                                 body=json.dumps(params))

    def start_logging(self, name=None):
        """
        Starts the processing of recording user activity events and
        log file delivery for a trail.

        :type name: string
        :param name: The name of the Trail for which CloudTrail logs events.

        """
        params = {}
        if name is not None:
            params['Name'] = name
        return self.make_request(action='StartLogging',
                                 body=json.dumps(params))

    def stop_logging(self, name=None):
        """
        Suspends the recording of user activity events and log file
        delivery for the specified trail. Under most circumstances,
        there is no need to use this action. You can update a trail
        without stopping it first. This action is the only way to stop
        logging activity.

        :type name: string
        :param name: Communicates to CloudTrail the name of the Trail for which
            to stop logging events.

        """
        params = {}
        if name is not None:
            params['Name'] = name
        return self.make_request(action='StopLogging',
                                 body=json.dumps(params))

    def update_trail(self, trail=None):
        """
        From the command line, use update-subscription.

        Updates the settings that specify delivery of log files.
        Changes to a trail do not require stopping the CloudTrail
        service. You can use this action to designate an existing
        bucket for log delivery, or to create a new bucket and prefix.
        If the existing bucket has previously been a target for
        CloudTrail log files, an IAM policy exists for the bucket. If
        you create a new bucket using UpdateTrail, you need to apply
        the policy to the bucket using one of the means provided by
        the Amazon S3 service.

        The request includes a Trail structure that specifies the
        following:


        + Trail name.
        + The name of the Amazon S3 bucket to which CloudTrail
          delivers your log files.
        + The name of the Amazon S3 key prefix that precedes each log
          file.
        + The name of the Amazon SNS topic that notifies you that a
          new file is available in your bucket.
        + Whether the log file should include events from global
          services, such as IAM or AWS STS.

        **CreateTrail** returns the appropriate HTTP status code if
        successful. If not, it returns either one of the common errors
        or one of the exceptions listed at the end of this page.

        :type trail: dict
        :param trail: Represents the Trail structure that contains the
            CloudTrail setting for an account.

        """
        params = {}
        if trail is not None:
            params['trail'] = trail
        return self.make_request(action='UpdateTrail',
                                 body=json.dumps(params))

    def make_request(self, action, body):
        headers = {
            'X-Amz-Target': '%s.%s' % (self.TargetPrefix, action),
            'Host': self.region.endpoint,
            'Content-Type': 'application/x-amz-json-1.1',
            'Content-Length': str(len(body)),
        }
        http_request = self.build_base_http_request(
            method='POST', path='/', auth_path='/', params={},
            headers=headers, data=body)
        response = self._mexe(http_request, sender=None,
                              override_num_retries=10)
        response_body = response.read()
        boto.log.debug(response_body)
        if response.status == 200:
            if response_body:
                return json.loads(response_body)
        else:
            json_body = json.loads(response_body)
            fault_name = json_body.get('__type', None)
            exception_class = self._faults.get(fault_name, self.ResponseError)
            raise exception_class(response.status, response.reason,
                                  body=json_body)


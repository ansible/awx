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
    time of the AWS API call, the source IP address, the request
    parameters, and the response elements returned by the service.

    As an alternative to using the API, you can use one of the AWS
    SDKs, which consist of libraries and sample code for various
    programming languages and platforms (Java, Ruby, .NET, iOS,
    Android, etc.). The SDKs provide a convenient way to create
    programmatic access to AWSCloudTrail. For example, the SDKs take
    care of cryptographically signing requests, managing errors, and
    retrying requests automatically. For information about the AWS
    SDKs, including how to download and install them, see the `Tools
    for Amazon Web Services page`_.

    See the CloudTrail User Guide for information about the data that
    is included with each AWS API call listed in the log files.
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
        "TrailNotProvidedException": exceptions.TrailNotProvidedException,
        "TrailNotFoundException": exceptions.TrailNotFoundException,
        "S3BucketDoesNotExistException": exceptions.S3BucketDoesNotExistException,
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

        super(CloudTrailConnection, self).__init__(**kwargs)
        self.region = region

    def _required_auth_capability(self):
        return ['hmac-v4']

    def create_trail(self, name=None, s3_bucket_name=None,
                     s3_key_prefix=None, sns_topic_name=None,
                     include_global_service_events=None, trail=None):
        """
        From the command line, use `create-subscription`.

        Creates a trail that specifies the settings for delivery of
        log data to an Amazon S3 bucket.

        Support for passing Trail as a parameter ends as early as
        February 25, 2014. The request and response examples in this
        topic show the use of parameters as well as a Trail object.
        Until Trail is removed, you can use either Trail or the
        parameter list.

        :type name: string
        :param name: Specifies the name of the trail.

        :type s3_bucket_name: string
        :param s3_bucket_name: Specifies the name of the Amazon S3 bucket
            designated for publishing log files.

        :type s3_key_prefix: string
        :param s3_key_prefix: Specifies the Amazon S3 key prefix that precedes
            the name of the bucket you have designated for log file delivery.

        :type sns_topic_name: string
        :param sns_topic_name: Specifies the name of the Amazon SNS topic
            defined for notification of log file delivery.

        :type include_global_service_events: boolean
        :param include_global_service_events: Specifies whether the trail is
            publishing events from global services such as IAM to the log
            files.

        :type trail: dict
        :param trail: Support for passing a Trail object in the CreateTrail or
            UpdateTrail actions will end as early as February 15, 2014. Instead
            of the Trail object and its members, use the parameters listed for
            these actions.

        """
        params = {}
        if name is not None:
            params['Name'] = name
        if s3_bucket_name is not None:
            params['S3BucketName'] = s3_bucket_name
        if s3_key_prefix is not None:
            params['S3KeyPrefix'] = s3_key_prefix
        if sns_topic_name is not None:
            params['SnsTopicName'] = sns_topic_name
        if include_global_service_events is not None:
            params['IncludeGlobalServiceEvents'] = include_global_service_events
        if trail is not None:
            params['trail'] = trail
        return self.make_request(action='CreateTrail',
                                 body=json.dumps(params))

    def delete_trail(self, name):
        """
        Deletes a trail.

        :type name: string
        :param name: The name of a trail to be deleted.

        """
        params = {'Name': name, }
        return self.make_request(action='DeleteTrail',
                                 body=json.dumps(params))

    def describe_trails(self, trail_name_list=None):
        """
        Retrieves the settings for some or all trails associated with
        an account.

        :type trail_name_list: list
        :param trail_name_list: The list of trails.

        """
        params = {}
        if trail_name_list is not None:
            params['trailNameList'] = trail_name_list
        return self.make_request(action='DescribeTrails',
                                 body=json.dumps(params))

    def get_trail_status(self, name):
        """
        Returns a JSON-formatted list of information about the
        specified trail. Fields include information on delivery
        errors, Amazon SNS and Amazon S3 errors, and start and stop
        logging times for each trail.

        The CloudTrail API is currently undergoing revision. This
        action currently returns both new fields and fields slated for
        removal from the API. The following lists indicate the plans
        for each field:

        **List of Members Planned for Ongoing Support**


        + IsLogging
        + LatestDeliveryTime
        + LatestNotificationTime
        + StartLoggingTime
        + StopLoggingTime
        + LatestNotificationError
        + LatestDeliveryError


        **List of Members Scheduled for Removal**


        + **LatestDeliveryAttemptTime**: Use LatestDeliveryTime
          instead.
        + **LatestNotificationAttemptTime**: Use
          LatestNotificationTime instead.
        + **LatestDeliveryAttemptSucceeded**: No replacement. See the
          note following this list.
        + **LatestNotificationAttemptSucceeded**: No replacement. See
          the note following this list.
        + **TimeLoggingStarted**: Use StartLoggingTime instead.
        + **TimeLoggingStopped**: Use StopLoggingtime instead.


        No replacements have been created for
        LatestDeliveryAttemptSucceeded and
        LatestNotificationAttemptSucceeded . Use LatestDeliveryError
        and LatestNotificationError to evaluate success or failure of
        log delivery or notification. Empty values returned for these
        fields indicate success. An error in LatestDeliveryError
        generally indicates either a missing bucket or insufficient
        permissions to write to the bucket. Similarly, an error in
        LatestNotificationError indicates either a missing topic or
        insufficient permissions.

        :type name: string
        :param name: The name of the trail for which you are requesting the
            current status.

        """
        params = {'Name': name, }
        return self.make_request(action='GetTrailStatus',
                                 body=json.dumps(params))

    def start_logging(self, name):
        """
        Starts the recording of AWS API calls and log file delivery
        for a trail.

        :type name: string
        :param name: The name of the trail for which CloudTrail logs AWS API
            calls.

        """
        params = {'Name': name, }
        return self.make_request(action='StartLogging',
                                 body=json.dumps(params))

    def stop_logging(self, name):
        """
        Suspends the recording of AWS API calls and log file delivery
        for the specified trail. Under most circumstances, there is no
        need to use this action. You can update a trail without
        stopping it first. This action is the only way to stop
        recording.

        :type name: string
        :param name: Communicates to CloudTrail the name of the trail for which
            to stop logging AWS API calls.

        """
        params = {'Name': name, }
        return self.make_request(action='StopLogging',
                                 body=json.dumps(params))

    def update_trail(self, name=None, s3_bucket_name=None,
                     s3_key_prefix=None, sns_topic_name=None,
                     include_global_service_events=None, trail=None):
        """
        From the command line, use `update-subscription`.

        Updates the settings that specify delivery of log files.
        Changes to a trail do not require stopping the CloudTrail
        service. Use this action to designate an existing bucket for
        log delivery. If the existing bucket has previously been a
        target for CloudTrail log files, an IAM policy exists for the
        bucket.

        Support for passing Trail as a parameter ends as early as
        February 25, 2014. The request and response examples in this
        topic show the use of parameters as well as a Trail object.
        Until Trail is removed, you can use either Trail or the
        parameter list.

        :type name: string
        :param name: Specifies the name of the trail.

        :type s3_bucket_name: string
        :param s3_bucket_name: Specifies the name of the Amazon S3 bucket
            designated for publishing log files.

        :type s3_key_prefix: string
        :param s3_key_prefix: Specifies the Amazon S3 key prefix that precedes
            the name of the bucket you have designated for log file delivery.

        :type sns_topic_name: string
        :param sns_topic_name: Specifies the name of the Amazon SNS topic
            defined for notification of log file delivery.

        :type include_global_service_events: boolean
        :param include_global_service_events: Specifies whether the trail is
            publishing events from global services such as IAM to the log
            files.

        :type trail: dict
        :param trail: Support for passing a Trail object in the CreateTrail or
            UpdateTrail actions will end as early as February 15, 2014. Instead
            of the Trail object and its members, use the parameters listed for
            these actions.

        """
        params = {}
        if name is not None:
            params['Name'] = name
        if s3_bucket_name is not None:
            params['S3BucketName'] = s3_bucket_name
        if s3_key_prefix is not None:
            params['S3KeyPrefix'] = s3_key_prefix
        if sns_topic_name is not None:
            params['SnsTopicName'] = sns_topic_name
        if include_global_service_events is not None:
            params['IncludeGlobalServiceEvents'] = include_global_service_events
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


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
from boto.sqs import exceptions


class SQSConnection(AWSQueryConnection):
    """
    Welcome to the Amazon Simple Queue Service API Reference . This
    section describes who should read this guide, how the guide is
    organized, and other resources related to the Amazon Simple Queue
    Service (Amazon SQS).

    Amazon SQS offers reliable and scalable hosted queues for storing
    messages as they travel between computers. By using Amazon SQS,
    you can move data between distributed components of your
    applications that perform different tasks without losing messages
    or requiring each component to be always available.

    Helpful Links:

    + `Current WSDL (2012-11-05)`_
    + `Making API Requests`_
    + `Amazon SQS product page`_
    + `Regions and Endpoints`_



    We also provide SDKs that enable you to access Amazon SQS from
    your preferred programming language. The SDKs contain
    functionality that automatically takes care of tasks such as:



    + Cryptographically signing your service requests
    + Retrying requests
    + Handling error responses



    For a list of available SDKs, go to `Tools for Amazon Web
    Services`_.
    """
    APIVersion = "2012-11-05"
    DefaultRegionName = "us-east-1"
    DefaultRegionEndpoint = "sqs.us-east-1.amazonaws.com"
    ResponseError = JSONResponseError

    _faults = {
        "QueueDoesNotExist": exceptions.QueueDoesNotExist,
        "BatchEntryIdsNotDistinct": exceptions.BatchEntryIdsNotDistinct,
        "EmptyBatchRequest": exceptions.EmptyBatchRequest,
        "OverLimit": exceptions.OverLimit,
        "QueueNameExists": exceptions.QueueNameExists,
        "InvalidMessageContents": exceptions.InvalidMessageContents,
        "TooManyEntriesInBatchRequest": exceptions.TooManyEntriesInBatchRequest,
        "QueueDeletedRecently": exceptions.QueueDeletedRecently,
        "InvalidBatchEntryId": exceptions.InvalidBatchEntryId,
        "BatchRequestTooLong": exceptions.BatchRequestTooLong,
        "InvalidIdFormat": exceptions.InvalidIdFormat,
        "ReceiptHandleIsInvalid": exceptions.ReceiptHandleIsInvalid,
        "InvalidAttributeName": exceptions.InvalidAttributeName,
        "MessageNotInflight": exceptions.MessageNotInflight,
    }


    def __init__(self, **kwargs):
        region = kwargs.pop('region', None)
        if not region:
            region = RegionInfo(self, self.DefaultRegionName,
                                self.DefaultRegionEndpoint)

        if 'host' not in kwargs:
            kwargs['host'] = region.endpoint

        super(SQSConnection, self).__init__(**kwargs)
        self.region = region

    def _required_auth_capability(self):
        return ['hmac-v4']

    def add_permission(self, queue_url, label, aws_account_ids, actions):
        """
        Adds a permission to a queue for a specific `principal`_. This
        allows for sharing access to the queue.

        When you create a queue, you have full control access rights
        for the queue. Only you (as owner of the queue) can grant or
        deny permissions to the queue. For more information about
        these permissions, see `Shared Queues`_ in the Amazon SQS
        Developer Guide .

        `AddPermission` writes an Amazon SQS-generated policy. If you
        want to write your own policy, use SetQueueAttributes to
        upload your policy. For more information about writing your
        own policy, see `Using The Access Policy Language`_ in the
        Amazon SQS Developer Guide .
        Some API actions take lists of parameters. These lists are
        specified using the `param.n` notation. Values of `n` are
        integers starting from 1. For example, a parameter list with
        two elements looks like this:
        `&Attribute.1=this`

        `&Attribute.2=that`

        :type queue_url: string
        :param queue_url: The URL of the Amazon SQS queue to take action on.

        :type label: string
        :param label: The unique identification of the permission you're
            setting (e.g., `AliceSendMessage`). Constraints: Maximum 80
            characters; alphanumeric characters, hyphens (-), and underscores
            (_) are allowed.

        :type aws_account_ids: list
        :param aws_account_ids: The AWS account number of the `principal`_ who
            will be given permission. The principal must have an AWS account,
            but does not need to be signed up for Amazon SQS. For information
            about locating the AWS account identification, see `Your AWS
            Identifiers`_ in the Amazon SQS Developer Guide .

        :type actions: list
        :param actions: The action the client wants to allow for the specified
            principal. The following are valid values: `* | SendMessage |
            ReceiveMessage | DeleteMessage | ChangeMessageVisibility |
            GetQueueAttributes | GetQueueUrl`. For more information about these
            actions, see `Understanding Permissions`_ in the Amazon SQS
            Developer Guide .
        Specifying `SendMessage`, `DeleteMessage`, or `ChangeMessageVisibility`
            for the `ActionName.n` also grants permissions for the
            corresponding batch versions of those actions: `SendMessageBatch`,
            `DeleteMessageBatch`, and `ChangeMessageVisibilityBatch`.

        """
        params = {'QueueUrl': queue_url, 'Label': label, }
        self.build_list_params(params,
                               aws_account_ids,
                               'AWSAccountIds.member')
        self.build_list_params(params,
                               actions,
                               'Actions.member')
        return self._make_request(
            action='AddPermission',
            verb='POST',
            path='/', params=params)

    def change_message_visibility(self, queue_url, receipt_handle,
                                  visibility_timeout):
        """
        Changes the visibility timeout of a specified message in a
        queue to a new value. The maximum allowed timeout value you
        can set the value to is 12 hours. This means you can't extend
        the timeout of a message in an existing queue to more than a
        total visibility timeout of 12 hours. (For more information
        visibility timeout, see `Visibility Timeout`_ in the Amazon
        SQS Developer Guide .)

        For example, let's say you have a message and its default
        message visibility timeout is 30 minutes. You could call
        `ChangeMessageVisiblity` with a value of two hours and the
        effective timeout would be two hours and 30 minutes. When that
        time comes near you could again extend the time out by calling
        ChangeMessageVisiblity, but this time the maximum allowed
        timeout would be 9 hours and 30 minutes.
        If you attempt to set the `VisibilityTimeout` to an amount
        more than the maximum time left, Amazon SQS returns an error.
        It will not automatically recalculate and increase the timeout
        to the maximum time remaining. Unlike with a queue, when you
        change the visibility timeout for a specific message, that
        timeout value is applied immediately but is not saved in
        memory for that message. If you don't delete a message after
        it is received, the visibility timeout for the message the
        next time it is received reverts to the original timeout
        value, not the value you set with the
        `ChangeMessageVisibility` action.

        :type queue_url: string
        :param queue_url: The URL of the Amazon SQS queue to take action on.

        :type receipt_handle: string
        :param receipt_handle: The receipt handle associated with the message
            whose visibility timeout should be changed. This parameter is
            returned by the ReceiveMessage action.

        :type visibility_timeout: integer
        :param visibility_timeout: The new value (in seconds - from 0 to 43200
            - maximum 12 hours) for the message's visibility timeout.

        """
        params = {
            'QueueUrl': queue_url,
            'ReceiptHandle': receipt_handle,
            'VisibilityTimeout': visibility_timeout,
        }
        return self._make_request(
            action='ChangeMessageVisibility',
            verb='POST',
            path='/', params=params)

    def change_message_visibility_batch(self, queue_url, entries):
        """
        Changes the visibility timeout of multiple messages. This is a
        batch version of ChangeMessageVisibility. The result of the
        action on each message is reported individually in the
        response. You can send up to 10 ChangeMessageVisibility
        requests with each `ChangeMessageVisibilityBatch` action.
        Because the batch request can result in a combination of
        successful and unsuccessful actions, you should check for
        batch errors even when the call returns an HTTP status code of
        200. Some API actions take lists of parameters. These lists
        are specified using the `param.n` notation. Values of `n` are
        integers starting from 1. For example, a parameter list with
        two elements looks like this:
        `&Attribute.1=this`

        `&Attribute.2=that`

        :type queue_url: string
        :param queue_url: The URL of the Amazon SQS queue to take action on.

        :type entries: list
        :param entries: A list of receipt handles of the messages for which the
            visibility timeout must be changed.

        """
        params = {'QueueUrl': queue_url, }
        self.build_complex_list_params(
            params, entries,
            'Entries.member',
            ('Id', 'ReceiptHandle', 'VisibilityTimeout'))
        return self._make_request(
            action='ChangeMessageVisibilityBatch',
            verb='POST',
            path='/', params=params)

    def create_queue(self, queue_name, attributes=None):
        """
        Creates a new queue, or returns the URL of an existing one.
        When you request `CreateQueue`, you provide a name for the
        queue. To successfully create a new queue, you must provide a
        name that is unique within the scope of your own queues.

        If you delete a queue, you must wait at least 60 seconds
        before creating a queue with the same name.

        You may pass one or more attributes in the request. If you do
        not provide a value for any attribute, the queue will have the
        default value for that attribute. Permitted attributes are the
        same that can be set using SetQueueAttributes.

        Use GetQueueUrl to get a queue's URL. GetQueueUrl requires
        only the `QueueName` parameter.

        If you provide the name of an existing queue, along with the
        exact names and values of all the queue's attributes,
        `CreateQueue` returns the queue URL for the existing queue. If
        the queue name, attribute names, or attribute values do not
        match an existing queue, `CreateQueue` returns an error.
        Some API actions take lists of parameters. These lists are
        specified using the `param.n` notation. Values of `n` are
        integers starting from 1. For example, a parameter list with
        two elements looks like this:
        `&Attribute.1=this`

        `&Attribute.2=that`

        :type queue_name: string
        :param queue_name: The name for the queue to be created.

        :type attributes: map
        :param attributes: A map of attributes with their corresponding values.
        The following lists the names, descriptions, and values of the special
            request parameters the `CreateQueue` action uses:



        + `DelaySeconds` - The time in seconds that the delivery of all
              messages in the queue will be delayed. An integer from 0 to 900 (15
              minutes). The default for this attribute is 0 (zero).
        + `MaximumMessageSize` - The limit of how many bytes a message can
              contain before Amazon SQS rejects it. An integer from 1024 bytes (1
              KiB) up to 262144 bytes (256 KiB). The default for this attribute
              is 262144 (256 KiB).
        + `MessageRetentionPeriod` - The number of seconds Amazon SQS retains a
              message. Integer representing seconds, from 60 (1 minute) to
              1209600 (14 days). The default for this attribute is 345600 (4
              days).
        + `Policy` - The queue's policy. A valid form-url-encoded policy. For
              more information about policy structure, see `Basic Policy
              Structure`_ in the Amazon SQS Developer Guide . For more
              information about form-url-encoding, see `http://www.w3.org/MarkUp
              /html-spec/html-spec_8.html#SEC8.2.1`_.
        + `ReceiveMessageWaitTimeSeconds` - The time for which a ReceiveMessage
              call will wait for a message to arrive. An integer from 0 to 20
              (seconds). The default for this attribute is 0.
        + `VisibilityTimeout` - The visibility timeout for the queue. An
              integer from 0 to 43200 (12 hours). The default for this attribute
              is 30. For more information about visibility timeout, see
              `Visibility Timeout`_ in the Amazon SQS Developer Guide .

        """
        params = {'QueueName': queue_name, }
        if attributes is not None:
            params['Attributes'] = attributes
        return self._make_request(
            action='CreateQueue',
            verb='POST',
            path='/', params=params)

    def delete_message(self, queue_url, receipt_handle):
        """
        Deletes the specified message from the specified queue. You
        specify the message by using the message's `receipt handle`
        and not the `message ID` you received when you sent the
        message. Even if the message is locked by another reader due
        to the visibility timeout setting, it is still deleted from
        the queue. If you leave a message in the queue for longer than
        the queue's configured retention period, Amazon SQS
        automatically deletes it.

        The receipt handle is associated with a specific instance of
        receiving the message. If you receive a message more than
        once, the receipt handle you get each time you receive the
        message is different. When you request `DeleteMessage`, if you
        don't provide the most recently received receipt handle for
        the message, the request will still succeed, but the message
        might not be deleted.

        It is possible you will receive a message even after you have
        deleted it. This might happen on rare occasions if one of the
        servers storing a copy of the message is unavailable when you
        request to delete the message. The copy remains on the server
        and might be returned to you again on a subsequent receive
        request. You should create your system to be idempotent so
        that receiving a particular message more than once is not a
        problem.

        :type queue_url: string
        :param queue_url: The URL of the Amazon SQS queue to take action on.

        :type receipt_handle: string
        :param receipt_handle: The receipt handle associated with the message
            to delete.

        """
        params = {
            'QueueUrl': queue_url,
            'ReceiptHandle': receipt_handle,
        }
        return self._make_request(
            action='DeleteMessage',
            verb='POST',
            path='/', params=params)

    def delete_message_batch(self, queue_url, entries):
        """
        Deletes multiple messages. This is a batch version of
        DeleteMessage. The result of the delete action on each message
        is reported individually in the response.

        Because the batch request can result in a combination of
        successful and unsuccessful actions, you should check for
        batch errors even when the call returns an HTTP status code of
        200.
        Some API actions take lists of parameters. These lists are
        specified using the `param.n` notation. Values of `n` are
        integers starting from 1. For example, a parameter list with
        two elements looks like this:
        `&Attribute.1=this`

        `&Attribute.2=that`

        :type queue_url: string
        :param queue_url: The URL of the Amazon SQS queue to take action on.

        :type entries: list
        :param entries: A list of receipt handles for the messages to be
            deleted.

        """
        params = {'QueueUrl': queue_url, }
        self.build_complex_list_params(
            params, entries,
            'Entries.member',
            ('Id', 'ReceiptHandle'))
        return self._make_request(
            action='DeleteMessageBatch',
            verb='POST',
            path='/', params=params)

    def delete_queue(self, queue_url):
        """
        Deletes the queue specified by the **queue URL**, regardless
        of whether the queue is empty. If the specified queue does not
        exist, Amazon SQS returns a successful response.

        Use `DeleteQueue` with care; once you delete your queue, any
        messages in the queue are no longer available.

        When you delete a queue, the deletion process takes up to 60
        seconds. Requests you send involving that queue during the 60
        seconds might succeed. For example, a SendMessage request
        might succeed, but after the 60 seconds, the queue and that
        message you sent no longer exist. Also, when you delete a
        queue, you must wait at least 60 seconds before creating a
        queue with the same name.

        We reserve the right to delete queues that have had no
        activity for more than 30 days. For more information, see `How
        Amazon SQS Queues Work`_ in the Amazon SQS Developer Guide .

        :type queue_url: string
        :param queue_url: The URL of the Amazon SQS queue to take action on.

        """
        params = {'QueueUrl': queue_url, }
        return self._make_request(
            action='DeleteQueue',
            verb='POST',
            path='/', params=params)

    def get_queue_attributes(self, queue_url, attribute_names=None):
        """
        Gets attributes for the specified queue. The following
        attributes are supported:

        + `All` - returns all values.
        + `ApproximateNumberOfMessages` - returns the approximate
          number of visible messages in a queue. For more information,
          see `Resources Required to Process Messages`_ in the Amazon
          SQS Developer Guide .
        + `ApproximateNumberOfMessagesNotVisible` - returns the
          approximate number of messages that are not timed-out and not
          deleted. For more information, see `Resources Required to
          Process Messages`_ in the Amazon SQS Developer Guide .
        + `VisibilityTimeout` - returns the visibility timeout for the
          queue. For more information about visibility timeout, see
          `Visibility Timeout`_ in the Amazon SQS Developer Guide .
        + `CreatedTimestamp` - returns the time when the queue was
          created (epoch time in seconds).
        + `LastModifiedTimestamp` - returns the time when the queue
          was last changed (epoch time in seconds).
        + `Policy` - returns the queue's policy.
        + `MaximumMessageSize` - returns the limit of how many bytes a
          message can contain before Amazon SQS rejects it.
        + `MessageRetentionPeriod` - returns the number of seconds
          Amazon SQS retains a message.
        + `QueueArn` - returns the queue's Amazon resource name (ARN).
        + `ApproximateNumberOfMessagesDelayed` - returns the
          approximate number of messages that are pending to be added to
          the queue.
        + `DelaySeconds` - returns the default delay on the queue in
          seconds.
        + `ReceiveMessageWaitTimeSeconds` - returns the time for which
          a ReceiveMessage call will wait for a message to arrive.
        + `RedrivePolicy` - returns the parameters for dead letter
          queue functionality of the source queue. For more information
          about RedrivePolicy and dead letter queues, see `Using Amazon
          SQS Dead Letter Queues`_ in the Amazon SQS Developer Guide .


        Going forward, new attributes might be added. If you are
        writing code that calls this action, we recommend that you
        structure your code so that it can handle new attributes
        gracefully. Some API actions take lists of parameters. These
        lists are specified using the `param.n` notation. Values of
        `n` are integers starting from 1. For example, a parameter
        list with two elements looks like this:
        `&Attribute.1=this`

        `&Attribute.2=that`

        :type queue_url: string
        :param queue_url: The URL of the Amazon SQS queue to take action on.

        :type attribute_names: list
        :param attribute_names: A list of attributes to retrieve information
            for.

        """
        params = {'QueueUrl': queue_url, }
        if attribute_names is not None:
            self.build_list_params(params,
                                   attribute_names,
                                   'AttributeNames.member')
        return self._make_request(
            action='GetQueueAttributes',
            verb='POST',
            path='/', params=params)

    def get_queue_url(self, queue_name, queue_owner_aws_account_id=None):
        """
        Returns the URL of an existing queue. This action provides a
        simple way to retrieve the URL of an Amazon SQS queue.

        To access a queue that belongs to another AWS account, use the
        `QueueOwnerAWSAccountId` parameter to specify the account ID
        of the queue's owner. The queue's owner must grant you
        permission to access the queue. For more information about
        shared queue access, see AddPermission or go to `Shared
        Queues`_ in the Amazon SQS Developer Guide .

        :type queue_name: string
        :param queue_name: The name of the queue whose URL must be fetched.
            Maximum 80 characters; alphanumeric characters, hyphens (-), and
            underscores (_) are allowed.

        :type queue_owner_aws_account_id: string
        :param queue_owner_aws_account_id: The AWS account ID of the account
            that created the queue.

        """
        params = {'QueueName': queue_name, }
        if queue_owner_aws_account_id is not None:
            params['QueueOwnerAWSAccountId'] = queue_owner_aws_account_id
        return self._make_request(
            action='GetQueueUrl',
            verb='POST',
            path='/', params=params)

    def list_dead_letter_source_queues(self, queue_url):
        """
        Returns a list of your queues that have the RedrivePolicy
        queue attribute configured with a dead letter queue.

        :type queue_url: string
        :param queue_url: The queue URL of a dead letter queue.

        """
        params = {'QueueUrl': queue_url, }
        return self._make_request(
            action='ListDeadLetterSourceQueues',
            verb='POST',
            path='/', params=params)

    def list_queues(self, queue_name_prefix=None):
        """
        Returns a list of your queues. The maximum number of queues
        that can be returned is 1000. If you specify a value for the
        optional `QueueNamePrefix` parameter, only queues with a name
        beginning with the specified value are returned.

        :type queue_name_prefix: string
        :param queue_name_prefix: A string to use for filtering the list
            results. Only those queues whose name begins with the specified
            string are returned.

        """
        params = {}
        if queue_name_prefix is not None:
            params['QueueNamePrefix'] = queue_name_prefix
        return self._make_request(
            action='ListQueues',
            verb='POST',
            path='/', params=params)

    def receive_message(self, queue_url, attribute_names=None,
                        max_number_of_messages=None, visibility_timeout=None,
                        wait_time_seconds=None):
        """
        Retrieves one or more messages from the specified queue. Long
        poll support is enabled by using the `WaitTimeSeconds`
        parameter. For more information, see `Amazon SQS Long Poll`_
        in the Amazon SQS Developer Guide .

        Short poll is the default behavior where a weighted random set
        of machines is sampled on a `ReceiveMessage` call. This means
        only the messages on the sampled machines are returned. If the
        number of messages in the queue is small (less than 1000), it
        is likely you will get fewer messages than you requested per
        `ReceiveMessage` call. If the number of messages in the queue
        is extremely small, you might not receive any messages in a
        particular `ReceiveMessage` response; in which case you should
        repeat the request.

        For each message returned, the response includes the
        following:


        + Message body
        + MD5 digest of the message body. For information about MD5,
          go to `http://www.faqs.org/rfcs/rfc1321.html`_.
        + Message ID you received when you sent the message to the
          queue.
        + Receipt handle.


        The receipt handle is the identifier you must provide when
        deleting the message. For more information, see `Queue and
        Message Identifiers`_ in the Amazon SQS Developer Guide .

        You can provide the `VisibilityTimeout` parameter in your
        request, which will be applied to the messages that Amazon SQS
        returns in the response. If you do not include the parameter,
        the overall visibility timeout for the queue is used for the
        returned messages. For more information, see `Visibility
        Timeout`_ in the Amazon SQS Developer Guide .

        Going forward, new attributes might be added. If you are
        writing code that calls this action, we recommend that you
        structure your code so that it can handle new attributes
        gracefully.

        :type queue_url: string
        :param queue_url: The URL of the Amazon SQS queue to take action on.

        :type attribute_names: list
        :param attribute_names:
        A list of attributes that need to be returned along with each message.

        The following lists the names and descriptions of the attributes that
            can be returned:


        + `All` - returns all values.
        + `ApproximateFirstReceiveTimestamp` - returns the time when the
              message was first received (epoch time in milliseconds).
        + `ApproximateReceiveCount` - returns the number of times a message has
              been received but not deleted.
        + `SenderId` - returns the AWS account number (or the IP address, if
              anonymous access is allowed) of the sender.
        + `SentTimestamp` - returns the time when the message was sent (epoch
              time in milliseconds).

        :type max_number_of_messages: integer
        :param max_number_of_messages: The maximum number of messages to
            return. Amazon SQS never returns more messages than this value but
            may return fewer.
        All of the messages are not necessarily returned.

        :type visibility_timeout: integer
        :param visibility_timeout: The duration (in seconds) that the received
            messages are hidden from subsequent retrieve requests after being
            retrieved by a `ReceiveMessage` request.

        :type wait_time_seconds: integer
        :param wait_time_seconds: The duration (in seconds) for which the call
            will wait for a message to arrive in the queue before returning. If
            a message is available, the call will return sooner than
            WaitTimeSeconds.

        """
        params = {'QueueUrl': queue_url, }
        if attribute_names is not None:
            self.build_list_params(params,
                                   attribute_names,
                                   'AttributeNames.member')
        if max_number_of_messages is not None:
            params['MaxNumberOfMessages'] = max_number_of_messages
        if visibility_timeout is not None:
            params['VisibilityTimeout'] = visibility_timeout
        if wait_time_seconds is not None:
            params['WaitTimeSeconds'] = wait_time_seconds
        return self._make_request(
            action='ReceiveMessage',
            verb='POST',
            path='/', params=params)

    def remove_permission(self, queue_url, label):
        """
        Revokes any permissions in the queue policy that matches the
        specified `Label` parameter. Only the owner of the queue can
        remove permissions.

        :type queue_url: string
        :param queue_url: The URL of the Amazon SQS queue to take action on.

        :type label: string
        :param label: The identification of the permission to remove. This is
            the label added with the AddPermission action.

        """
        params = {'QueueUrl': queue_url, 'Label': label, }
        return self._make_request(
            action='RemovePermission',
            verb='POST',
            path='/', params=params)

    def send_message(self, queue_url, message_body, delay_seconds=None):
        """
        Delivers a message to the specified queue. With Amazon SQS,
        you now have the ability to send large payload messages that
        are up to 256KB (262,144 bytes) in size. To send large
        payloads, you must use an AWS SDK that supports SigV4 signing.
        To verify whether SigV4 is supported for an AWS SDK, check the
        SDK release notes.

        The following list shows the characters (in Unicode) allowed
        in your message, according to the W3C XML specification. For
        more information, go to `http://www.w3.org/TR/REC-
        xml/#charsets`_ If you send any characters not included in the
        list, your request will be rejected.

        #x9 | #xA | #xD | [#x20 to #xD7FF] | [#xE000 to #xFFFD] |
        [#x10000 to #x10FFFF]

        :type queue_url: string
        :param queue_url: The URL of the Amazon SQS queue to take action on.

        :type message_body: string
        :param message_body: The message to send. String maximum 256 KB in
            size. For a list of allowed characters, see the preceding important
            note.

        :type delay_seconds: integer
        :param delay_seconds: The number of seconds (0 to 900 - 15 minutes) to
            delay a specific message. Messages with a positive `DelaySeconds`
            value become available for processing after the delay time is
            finished. If you don't specify a value, the default value for the
            queue applies.

        """
        params = {
            'QueueUrl': queue_url,
            'MessageBody': message_body,
        }
        if delay_seconds is not None:
            params['DelaySeconds'] = delay_seconds
        return self._make_request(
            action='SendMessage',
            verb='POST',
            path='/', params=params)

    def send_message_batch(self, queue_url, entries):
        """
        Delivers up to ten messages to the specified queue. This is a
        batch version of SendMessage. The result of the send action on
        each message is reported individually in the response. The
        maximum allowed individual message size is 256 KB (262,144
        bytes).

        The maximum total payload size (i.e., the sum of all a batch's
        individual message lengths) is also 256 KB (262,144 bytes).

        If the `DelaySeconds` parameter is not specified for an entry,
        the default for the queue is used.
        The following list shows the characters (in Unicode) that are
        allowed in your message, according to the W3C XML
        specification. For more information, go to
        `http://www.faqs.org/rfcs/rfc1321.html`_. If you send any
        characters that are not included in the list, your request
        will be rejected.
        #x9 | #xA | #xD | [#x20 to #xD7FF] | [#xE000 to #xFFFD] |
        [#x10000 to #x10FFFF]
        Because the batch request can result in a combination of
        successful and unsuccessful actions, you should check for
        batch errors even when the call returns an HTTP status code of
        200. Some API actions take lists of parameters. These lists
        are specified using the `param.n` notation. Values of `n` are
        integers starting from 1. For example, a parameter list with
        two elements looks like this:
        `&Attribute.1=this`

        `&Attribute.2=that`

        :type queue_url: string
        :param queue_url: The URL of the Amazon SQS queue to take action on.

        :type entries: list
        :param entries: A list of SendMessageBatchRequestEntry items.

        """
        params = {'QueueUrl': queue_url, }
        self.build_complex_list_params(
            params, entries,
            'Entries.member',
            ('Id', 'MessageBody', 'DelaySeconds'))
        return self._make_request(
            action='SendMessageBatch',
            verb='POST',
            path='/', params=params)

    def set_queue_attributes(self, queue_url, attributes):
        """
        Sets the value of one or more queue attributes.
        Going forward, new attributes might be added. If you are
        writing code that calls this action, we recommend that you
        structure your code so that it can handle new attributes
        gracefully.

        :type queue_url: string
        :param queue_url: The URL of the Amazon SQS queue to take action on.

        :type attributes: map
        :param attributes: A map of attributes to set.
        The following lists the names, descriptions, and values of the special
            request parameters the `SetQueueAttributes` action uses:



        + `DelaySeconds` - The time in seconds that the delivery of all
              messages in the queue will be delayed. An integer from 0 to 900 (15
              minutes). The default for this attribute is 0 (zero).
        + `MaximumMessageSize` - The limit of how many bytes a message can
              contain before Amazon SQS rejects it. An integer from 1024 bytes (1
              KiB) up to 262144 bytes (256 KiB). The default for this attribute
              is 262144 (256 KiB).
        + `MessageRetentionPeriod` - The number of seconds Amazon SQS retains a
              message. Integer representing seconds, from 60 (1 minute) to
              1209600 (14 days). The default for this attribute is 345600 (4
              days).
        + `Policy` - The queue's policy. A valid form-url-encoded policy. For
              more information about policy structure, see `Basic Policy
              Structure`_ in the Amazon SQS Developer Guide . For more
              information about form-url-encoding, see `http://www.w3.org/MarkUp
              /html-spec/html-spec_8.html#SEC8.2.1`_.
        + `ReceiveMessageWaitTimeSeconds` - The time for which a ReceiveMessage
              call will wait for a message to arrive. An integer from 0 to 20
              (seconds). The default for this attribute is 0.
        + `VisibilityTimeout` - The visibility timeout for the queue. An
              integer from 0 to 43200 (12 hours). The default for this attribute
              is 30. For more information about visibility timeout, see
              Visibility Timeout in the Amazon SQS Developer Guide .
        + `RedrivePolicy` - The parameters for dead letter queue functionality
              of the source queue. For more information about RedrivePolicy and
              dead letter queues, see Using Amazon SQS Dead Letter Queues in the
              Amazon SQS Developer Guide .

        """
        params = {'QueueUrl': queue_url, }
        # TODO: NEED TO PROCESS COMPLEX ARG attributes of type map.
        return self._make_request(
            action='SetQueueAttributes',
            verb='POST',
            path='/', params=params)

    def _make_request(self, action, verb, path, params):
        params['ContentType'] = 'JSON'
        response = self.make_request(action=action, verb='POST',
                                     path='/', params=params)
        body = response.read()
        boto.log.debug(body)
        if response.status == 200:
            return json.loads(body)
        else:
            json_body = json.loads(body)
            fault_name = json_body.get('Error', {}).get('Code', None)
            exception_class = self._faults.get(fault_name, self.ResponseError)
            raise exception_class(response.status, response.reason,
                                  body=json_body)

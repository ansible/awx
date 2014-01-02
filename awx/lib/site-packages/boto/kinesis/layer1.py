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

import base64
import boto

from boto.connection import AWSQueryConnection
from boto.regioninfo import RegionInfo
from boto.exception import JSONResponseError
from boto.kinesis import exceptions


class KinesisConnection(AWSQueryConnection):
    """
    Amazon Kinesis Service API Reference
    Amazon Kinesis is a managed service that scales elastically for
    real time processing of streaming big data.
    """
    APIVersion = "2013-12-02"
    DefaultRegionName = "us-east-1"
    DefaultRegionEndpoint = "kinesis.us-east-1.amazonaws.com"
    ServiceName = "Kinesis"
    TargetPrefix = "Kinesis_20131202"
    ResponseError = JSONResponseError

    _faults = {
        "ProvisionedThroughputExceededException": exceptions.ProvisionedThroughputExceededException,
        "LimitExceededException": exceptions.LimitExceededException,
        "ExpiredIteratorException": exceptions.ExpiredIteratorException,
        "ResourceInUseException": exceptions.ResourceInUseException,
        "ResourceNotFoundException": exceptions.ResourceNotFoundException,
        "InvalidArgumentException": exceptions.InvalidArgumentException,
        "SubscriptionRequiredException": exceptions.SubscriptionRequiredException
    }


    def __init__(self, **kwargs):
        region = kwargs.pop('region', None)
        if not region:
            region = RegionInfo(self, self.DefaultRegionName,
                                self.DefaultRegionEndpoint)
        if 'host' not in kwargs:
            kwargs['host'] = region.endpoint
        super(KinesisConnection, self).__init__(**kwargs)
        self.region = region

    def _required_auth_capability(self):
        return ['hmac-v4']

    def create_stream(self, stream_name, shard_count):
        """
        This operation adds a new Amazon Kinesis stream to your AWS
        account. A stream captures and transports data records that
        are continuously emitted from different data sources or
        producers . Scale-out within an Amazon Kinesis stream is
        explicitly supported by means of shards, which are uniquely
        identified groups of data records in an Amazon Kinesis stream.

        You specify and control the number of shards that a stream is
        composed of. Each shard can support up to 5 read transactions
        per second up to a maximum total of 2 MB of data read per
        second. Each shard can support up to 1000 write transactions
        per second up to a maximum total of 1 MB data written per
        second. You can add shards to a stream if the amount of data
        input increases and you can remove shards if the amount of
        data input decreases.

        The stream name identifies the stream. The name is scoped to
        the AWS account used by the application. It is also scoped by
        region. That is, two streams in two different accounts can
        have the same name, and two streams in the same account, but
        in two different regions, can have the same name.

        `CreateStream` is an asynchronous operation. Upon receiving a
        `CreateStream` request, Amazon Kinesis immediately returns and
        sets the stream status to CREATING. After the stream is
        created, Amazon Kinesis sets the stream status to ACTIVE. You
        should perform read and write operations only on an ACTIVE
        stream.

        You receive a `LimitExceededException` when making a
        `CreateStream` request if you try to do one of the following:


        + Have more than five streams in the CREATING state at any
          point in time.
        + Create more shards than are authorized for your account.


        **Note:** The default limit for an AWS account is two shards
        per stream. If you need to create a stream with more than two
        shards, contact AWS Support to increase the limit on your
        account.

        You can use the `DescribeStream` operation to check the stream
        status, which is returned in `StreamStatus`.

        `CreateStream` has a limit of 5 transactions per second per
        account.

        :type stream_name: string
        :param stream_name: A name to identify the stream. The stream name is
            scoped to the AWS account used by the application that creates the
            stream. It is also scoped by region. That is, two streams in two
            different AWS accounts can have the same name, and two streams in
            the same AWS account, but in two different regions, can have the
            same name.

        :type shard_count: integer
        :param shard_count: The number of shards that the stream will use. The
            throughput of the stream is a function of the number of shards;
            more shards are required for greater provisioned throughput.
        **Note:** The default limit for an AWS account is two shards per
            stream. If you need to create a stream with more than two shards,
            contact AWS Support to increase the limit on your account.

        """
        params = {
            'StreamName': stream_name,
            'ShardCount': shard_count,
        }
        return self.make_request(action='CreateStream',
                                 body=json.dumps(params))

    def delete_stream(self, stream_name):
        """
        This operation deletes a stream and all of its shards and
        data. You must shut down any applications that are operating
        on the stream before you delete the stream. If an application
        attempts to operate on a deleted stream, it will receive the
        exception `ResourceNotFoundException`.

        If the stream is in the ACTIVE state, you can delete it. After
        a `DeleteStream` request, the specified stream is in the
        DELETING state until Amazon Kinesis completes the deletion.

        **Note:** Amazon Kinesis might continue to accept data read
        and write operations, such as PutRecord and GetRecords, on a
        stream in the DELETING state until the stream deletion is
        complete.

        When you delete a stream, any shards in that stream are also
        deleted.

        You can use the DescribeStream operation to check the state of
        the stream, which is returned in `StreamStatus`.

        `DeleteStream` has a limit of 5 transactions per second per
        account.

        :type stream_name: string
        :param stream_name: The name of the stream to delete.

        """
        params = {'StreamName': stream_name, }
        return self.make_request(action='DeleteStream',
                                 body=json.dumps(params))

    def describe_stream(self, stream_name, limit=None,
                        exclusive_start_shard_id=None):
        """
        This operation returns the following information about the
        stream: the current status of the stream, the stream Amazon
        Resource Name (ARN), and an array of shard objects that
        comprise the stream. For each shard object there is
        information about the hash key and sequence number ranges that
        the shard spans, and the IDs of any earlier shards that played
        in a role in a MergeShards or SplitShard operation that
        created the shard. A sequence number is the identifier
        associated with every record ingested in the Amazon Kinesis
        stream. The sequence number is assigned by the Amazon Kinesis
        service when a record is put into the stream.

        You can limit the number of returned shards using the `Limit`
        parameter. The number of shards in a stream may be too large
        to return from a single call to `DescribeStream`. You can
        detect this by using the `HasMoreShards` flag in the returned
        output. `HasMoreShards` is set to `True` when there is more
        data available.

        If there are more shards available, you can request more
        shards by using the shard ID of the last shard returned by the
        `DescribeStream` request, in the `ExclusiveStartShardId`
        parameter in a subsequent request to `DescribeStream`.
        `DescribeStream` is a paginated operation.

        `DescribeStream` has a limit of 10 transactions per second per
        account.

        :type stream_name: string
        :param stream_name: The name of the stream to describe.

        :type limit: integer
        :param limit: The maximum number of shards to return.

        :type exclusive_start_shard_id: string
        :param exclusive_start_shard_id: The shard ID of the shard to start
            with for the stream description.

        """
        params = {'StreamName': stream_name, }
        if limit is not None:
            params['Limit'] = limit
        if exclusive_start_shard_id is not None:
            params['ExclusiveStartShardId'] = exclusive_start_shard_id
        return self.make_request(action='DescribeStream',
                                 body=json.dumps(params))

    def get_records(self, shard_iterator, limit=None, b64_decode=True):
        """
        This operation returns one or more data records from a shard.
        A `GetRecords` operation request can retrieve up to 10 MB of
        data.

        You specify a shard iterator for the shard that you want to
        read data from in the `ShardIterator` parameter. The shard
        iterator specifies the position in the shard from which you
        want to start reading data records sequentially. A shard
        iterator specifies this position using the sequence number of
        a data record in the shard. For more information about the
        shard iterator, see GetShardIterator.

        `GetRecords` may return a partial result if the response size
        limit is exceeded. You will get an error, but not a partial
        result if the shard's provisioned throughput is exceeded, the
        shard iterator has expired, or an internal processing failure
        has occurred. Clients can request a smaller amount of data by
        specifying a maximum number of returned records using the
        `Limit` parameter. The `Limit` parameter can be set to an
        integer value of up to 10,000. If you set the value to an
        integer greater than 10,000, you will receive
        `InvalidArgumentException`.

        A new shard iterator is returned by every `GetRecords` request
        in `NextShardIterator`, which you use in the `ShardIterator`
        parameter of the next `GetRecords` request. When you
        repeatedly read from an Amazon Kinesis stream use a
        GetShardIterator request to get the first shard iterator to
        use in your first `GetRecords` request and then use the shard
        iterator returned in `NextShardIterator` for subsequent reads.

        `GetRecords` can return `null` for the `NextShardIterator` to
        reflect that the shard has been closed and that the requested
        shard iterator would never have returned more data.

        If no items can be processed because of insufficient
        provisioned throughput on the shard involved in the request,
        `GetRecords` throws `ProvisionedThroughputExceededException`.

        :type shard_iterator: string
        :param shard_iterator: The position in the shard from which you want to
            start sequentially reading data records.

        :type limit: integer
        :param limit: The maximum number of records to return, which can be set
            to a value of up to 10,000.

        :type b64_decode: boolean
        :param b64_decode: Decode the Base64-encoded ``Data`` field of records.

        """
        params = {'ShardIterator': shard_iterator, }
        if limit is not None:
            params['Limit'] = limit

        response = self.make_request(action='GetRecords',
                                     body=json.dumps(params))

        # Base64 decode the data
        if b64_decode:
            for record in response.get('Records', []):
                record['Data'] = base64.b64decode(record['Data'])

        return response

    def get_shard_iterator(self, stream_name, shard_id, shard_iterator_type,
                           starting_sequence_number=None):
        """
        This operation returns a shard iterator in `ShardIterator`.
        The shard iterator specifies the position in the shard from
        which you want to start reading data records sequentially. A
        shard iterator specifies this position using the sequence
        number of a data record in a shard. A sequence number is the
        identifier associated with every record ingested in the Amazon
        Kinesis stream. The sequence number is assigned by the Amazon
        Kinesis service when a record is put into the stream.

        You must specify the shard iterator type in the
        `GetShardIterator` request. For example, you can set the
        `ShardIteratorType` parameter to read exactly from the
        position denoted by a specific sequence number by using the
        AT_SEQUENCE_NUMBER shard iterator type, or right after the
        sequence number by using the AFTER_SEQUENCE_NUMBER shard
        iterator type, using sequence numbers returned by earlier
        PutRecord, GetRecords or DescribeStream requests. You can
        specify the shard iterator type TRIM_HORIZON in the request to
        cause `ShardIterator` to point to the last untrimmed record in
        the shard in the system, which is the oldest data record in
        the shard. Or you can point to just after the most recent
        record in the shard, by using the shard iterator type LATEST,
        so that you always read the most recent data in the shard.

        **Note:** Each shard iterator expires five minutes after it is
        returned to the requester.

        When you repeatedly read from an Amazon Kinesis stream use a
        GetShardIterator request to get the first shard iterator to to
        use in your first `GetRecords` request and then use the shard
        iterator returned by the `GetRecords` request in
        `NextShardIterator` for subsequent reads. A new shard iterator
        is returned by every `GetRecords` request in
        `NextShardIterator`, which you use in the `ShardIterator`
        parameter of the next `GetRecords` request.

        If a `GetShardIterator` request is made too often, you will
        receive a `ProvisionedThroughputExceededException`. For more
        information about throughput limits, see the `Amazon Kinesis
        Developer Guide`_.

        `GetShardIterator` can return `null` for its `ShardIterator`
        to indicate that the shard has been closed and that the
        requested iterator will return no more data. A shard can be
        closed by a SplitShard or MergeShards operation.

        `GetShardIterator` has a limit of 5 transactions per second
        per account per shard.

        :type stream_name: string
        :param stream_name: The name of the stream.

        :type shard_id: string
        :param shard_id: The shard ID of the shard to get the iterator for.

        :type shard_iterator_type: string
        :param shard_iterator_type:
        Determines how the shard iterator is used to start reading data records
            from the shard.

        The following are the valid shard iterator types:


        + AT_SEQUENCE_NUMBER - Start reading exactly from the position denoted
              by a specific sequence number.
        + AFTER_SEQUENCE_NUMBER - Start reading right after the position
              denoted by a specific sequence number.
        + TRIM_HORIZON - Start reading at the last untrimmed record in the
              shard in the system, which is the oldest data record in the shard.
        + LATEST - Start reading just after the most recent record in the
              shard, so that you always read the most recent data in the shard.

        :type starting_sequence_number: string
        :param starting_sequence_number: The sequence number of the data record
            in the shard from which to start reading from.

        """
        params = {
            'StreamName': stream_name,
            'ShardId': shard_id,
            'ShardIteratorType': shard_iterator_type,
        }
        if starting_sequence_number is not None:
            params['StartingSequenceNumber'] = starting_sequence_number
        return self.make_request(action='GetShardIterator',
                                 body=json.dumps(params))

    def list_streams(self, limit=None, exclusive_start_stream_name=None):
        """
        This operation returns an array of the names of all the
        streams that are associated with the AWS account making the
        `ListStreams` request. A given AWS account can have many
        streams active at one time.

        The number of streams may be too large to return from a single
        call to `ListStreams`. You can limit the number of returned
        streams using the `Limit` parameter. If you do not specify a
        value for the `Limit` parameter, Amazon Kinesis uses the
        default limit, which is currently 10.

        You can detect if there are more streams available to list by
        using the `HasMoreStreams` flag from the returned output. If
        there are more streams available, you can request more streams
        by using the name of the last stream returned by the
        `ListStreams` request in the `ExclusiveStartStreamName`
        parameter in a subsequent request to `ListStreams`. The group
        of stream names returned by the subsequent request is then
        added to the list. You can continue this process until all the
        stream names have been collected in the list.

        `ListStreams` has a limit of 5 transactions per second per
        account.

        :type limit: integer
        :param limit: The maximum number of streams to list.

        :type exclusive_start_stream_name: string
        :param exclusive_start_stream_name: The name of the stream to start the
            list with.

        """
        params = {}
        if limit is not None:
            params['Limit'] = limit
        if exclusive_start_stream_name is not None:
            params['ExclusiveStartStreamName'] = exclusive_start_stream_name
        return self.make_request(action='ListStreams',
                                 body=json.dumps(params))

    def merge_shards(self, stream_name, shard_to_merge,
                     adjacent_shard_to_merge):
        """
        This operation merges two adjacent shards in a stream and
        combines them into a single shard to reduce the stream's
        capacity to ingest and transport data. Two shards are
        considered adjacent if the union of the hash key ranges for
        the two shards form a contiguous set with no gaps. For
        example, if you have two shards, one with a hash key range of
        276...381 and the other with a hash key range of 382...454,
        then you could merge these two shards into a single shard that
        would have a hash key range of 276...454. After the merge, the
        single child shard receives data for all hash key values
        covered by the two parent shards.

        `MergeShards` is called when there is a need to reduce the
        overall capacity of a stream because of excess capacity that
        is not being used. The operation requires that you specify the
        shard to be merged and the adjacent shard for a given stream.
        For more information about merging shards, see the `Amazon
        Kinesis Developer Guide`_.

        If the stream is in the ACTIVE state, you can call
        `MergeShards`. If a stream is in CREATING or UPDATING or
        DELETING states, then Amazon Kinesis returns a
        `ResourceInUseException`. If the specified stream does not
        exist, Amazon Kinesis returns a `ResourceNotFoundException`.

        You can use the DescribeStream operation to check the state of
        the stream, which is returned in `StreamStatus`.

        `MergeShards` is an asynchronous operation. Upon receiving a
        `MergeShards` request, Amazon Kinesis immediately returns a
        response and sets the `StreamStatus` to UPDATING. After the
        operation is completed, Amazon Kinesis sets the `StreamStatus`
        to ACTIVE. Read and write operations continue to work while
        the stream is in the UPDATING state.

        You use the DescribeStream operation to determine the shard
        IDs that are specified in the `MergeShards` request.

        If you try to operate on too many streams in parallel using
        CreateStream, DeleteStream, `MergeShards` or SplitShard, you
        will receive a `LimitExceededException`.

        `MergeShards` has limit of 5 transactions per second per
        account.

        :type stream_name: string
        :param stream_name: The name of the stream for the merge.

        :type shard_to_merge: string
        :param shard_to_merge: The shard ID of the shard to combine with the
            adjacent shard for the merge.

        :type adjacent_shard_to_merge: string
        :param adjacent_shard_to_merge: The shard ID of the adjacent shard for
            the merge.

        """
        params = {
            'StreamName': stream_name,
            'ShardToMerge': shard_to_merge,
            'AdjacentShardToMerge': adjacent_shard_to_merge,
        }
        return self.make_request(action='MergeShards',
                                 body=json.dumps(params))

    def put_record(self, stream_name, data, partition_key,
                   explicit_hash_key=None,
                   sequence_number_for_ordering=None,
                   exclusive_minimum_sequence_number=None,
                   b64_encode=True):
        """
        This operation puts a data record into an Amazon Kinesis
        stream from a producer. This operation must be called to send
        data from the producer into the Amazon Kinesis stream for
        real-time ingestion and subsequent processing. The `PutRecord`
        operation requires the name of the stream that captures,
        stores, and transports the data; a partition key; and the data
        blob itself. The data blob could be a segment from a log file,
        geographic/location data, website clickstream data, or any
        other data type.

        The partition key is used to distribute data across shards.
        Amazon Kinesis segregates the data records that belong to a
        data stream into multiple shards, using the partition key
        associated with each data record to determine which shard a
        given data record belongs to.

        Partition keys are Unicode strings, with a maximum length
        limit of 256 bytes. An MD5 hash function is used to map
        partition keys to 128-bit integer values and to map associated
        data records to shards using the hash key ranges of the
        shards. You can override hashing the partition key to
        determine the shard by explicitly specifying a hash value
        using the `ExplicitHashKey` parameter. For more information,
        see the `Amazon Kinesis Developer Guide`_.

        `PutRecord` returns the shard ID of where the data record was
        placed and the sequence number that was assigned to the data
        record.

        The `SequenceNumberForOrdering` sets the initial sequence
        number for the partition key. Later `PutRecord` requests to
        the same partition key (from the same client) will
        automatically increase from `SequenceNumberForOrdering`,
        ensuring strict sequential ordering.

        If a `PutRecord` request cannot be processed because of
        insufficient provisioned throughput on the shard involved in
        the request, `PutRecord` throws
        `ProvisionedThroughputExceededException`.

        Data records are accessible for only 24 hours from the time
        that they are added to an Amazon Kinesis stream.

        :type stream_name: string
        :param stream_name: The name of the stream to put the data record into.

        :type data: blob
        :param data: The data blob to put into the record, which will be Base64
            encoded. The maximum size of the data blob is 50 kilobytes (KB).
            Set `b64_encode` to disable automatic Base64 encoding.

        :type partition_key: string
        :param partition_key: Determines which shard in the stream the data
            record is assigned to. Partition keys are Unicode strings with a
            maximum length limit of 256 bytes. Amazon Kinesis uses the
            partition key as input to a hash function that maps the partition
            key and associated data to a specific shard. Specifically, an MD5
            hash function is used to map partition keys to 128-bit integer
            values and to map associated data records to shards. As a result of
            this hashing mechanism, all data records with the same partition
            key will map to the same shard within the stream.

        :type explicit_hash_key: string
        :param explicit_hash_key: The hash value used to explicitly determine
            the shard the data record is assigned to by overriding the
            partition key hash.

        :type sequence_number_for_ordering: string
        :param sequence_number_for_ordering: The sequence number to use as the
            initial number for the partition key. Subsequent calls to
            `PutRecord` from the same client and for the same partition key
            will increase from the `SequenceNumberForOrdering` value.

        :type b64_encode: boolean
        :param b64_encode: Whether to Base64 encode `data`. Can be set to
            ``False`` if `data` is already encoded to prevent double encoding.

        """
        params = {
            'StreamName': stream_name,
            'Data': data,
            'PartitionKey': partition_key,
        }
        if explicit_hash_key is not None:
            params['ExplicitHashKey'] = explicit_hash_key
        if sequence_number_for_ordering is not None:
            params['SequenceNumberForOrdering'] = sequence_number_for_ordering
        if b64_encode:
            params['Data'] = base64.b64encode(params['Data'])
        return self.make_request(action='PutRecord',
                                 body=json.dumps(params))

    def split_shard(self, stream_name, shard_to_split, new_starting_hash_key):
        """
        This operation splits a shard into two new shards in the
        stream, to increase the stream's capacity to ingest and
        transport data. `SplitShard` is called when there is a need to
        increase the overall capacity of stream because of an expected
        increase in the volume of data records being ingested.

        `SplitShard` can also be used when a given shard appears to be
        approaching its maximum utilization, for example, when the set
        of producers sending data into the specific shard are suddenly
        sending more than previously anticipated. You can also call
        the `SplitShard` operation to increase stream capacity, so
        that more Amazon Kinesis applications can simultaneously read
        data from the stream for real-time processing.

        The `SplitShard` operation requires that you specify the shard
        to be split and the new hash key, which is the position in the
        shard where the shard gets split in two. In many cases, the
        new hash key might simply be the average of the beginning and
        ending hash key, but it can be any hash key value in the range
        being mapped into the shard. For more information about
        splitting shards, see the `Amazon Kinesis Developer Guide`_.

        You can use the DescribeStream operation to determine the
        shard ID and hash key values for the `ShardToSplit` and
        `NewStartingHashKey` parameters that are specified in the
        `SplitShard` request.

        `SplitShard` is an asynchronous operation. Upon receiving a
        `SplitShard` request, Amazon Kinesis immediately returns a
        response and sets the stream status to UPDATING. After the
        operation is completed, Amazon Kinesis sets the stream status
        to ACTIVE. Read and write operations continue to work while
        the stream is in the UPDATING state.

        You can use `DescribeStream` to check the status of the
        stream, which is returned in `StreamStatus`. If the stream is
        in the ACTIVE state, you can call `SplitShard`. If a stream is
        in CREATING or UPDATING or DELETING states, then Amazon
        Kinesis returns a `ResourceInUseException`.

        If the specified stream does not exist, Amazon Kinesis returns
        a `ResourceNotFoundException`. If you try to create more
        shards than are authorized for your account, you receive a
        `LimitExceededException`.

        **Note:** The default limit for an AWS account is two shards
        per stream. If you need to create a stream with more than two
        shards, contact AWS Support to increase the limit on your
        account.

        If you try to operate on too many streams in parallel using
        CreateStream, DeleteStream, MergeShards or SplitShard, you
        will receive a `LimitExceededException`.

        `SplitShard` has limit of 5 transactions per second per
        account.

        :type stream_name: string
        :param stream_name: The name of the stream for the shard split.

        :type shard_to_split: string
        :param shard_to_split: The shard ID of the shard to split.

        :type new_starting_hash_key: string
        :param new_starting_hash_key: A hash key value for the starting hash
            key of one of the child shards created by the split. The hash key
            range for a given shard constitutes a set of ordered contiguous
            positive integers. The value for `NewStartingHashKey` must be in
            the range of hash keys being mapped into the shard. The
            `NewStartingHashKey` hash key value and all higher hash key values
            in hash key range are distributed to one of the child shards. All
            the lower hash key values in the range are distributed to the other
            child shard.

        """
        params = {
            'StreamName': stream_name,
            'ShardToSplit': shard_to_split,
            'NewStartingHashKey': new_starting_hash_key,
        }
        return self.make_request(action='SplitShard',
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
        boto.log.debug(response.getheaders())
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


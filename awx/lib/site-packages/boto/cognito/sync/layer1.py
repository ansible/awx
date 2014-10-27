# Copyright (c) 2014 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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
from boto.compat import json
from boto.exception import JSONResponseError
from boto.connection import AWSAuthConnection
from boto.regioninfo import RegionInfo
from boto.cognito.sync import exceptions


class CognitoSyncConnection(AWSAuthConnection):
    """
    Amazon Cognito Sync
    Amazon Cognito Sync provides an AWS service and client library
    that enable cross-device syncing of application-related user data.
    High-level client libraries are available for both iOS and
    Android. You can use these libraries to persist data locally so
    that it's available even if the device is offline. Developer
    credentials don't need to be stored on the mobile device to access
    the service. You can use Amazon Cognito to obtain a normalized
    user ID and credentials. User data is persisted in a dataset that
    can store up to 1 MB of key-value pairs, and you can have up to 20
    datasets per user identity.
    """
    APIVersion = "2014-06-30"
    DefaultRegionName = "us-east-1"
    DefaultRegionEndpoint = "cognito-sync.us-east-1.amazonaws.com"
    ResponseError = JSONResponseError

    _faults = {
        "LimitExceededException": exceptions.LimitExceededException,
        "ResourceConflictException": exceptions.ResourceConflictException,
        "TooManyRequestsException": exceptions.TooManyRequestsException,
        "InvalidParameterException": exceptions.InvalidParameterException,
        "ResourceNotFoundException": exceptions.ResourceNotFoundException,
        "InternalErrorException": exceptions.InternalErrorException,
        "NotAuthorizedException": exceptions.NotAuthorizedException,
    }


    def __init__(self, **kwargs):
        region = kwargs.get('region')
        if not region:
            region = RegionInfo(self, self.DefaultRegionName,
                                self.DefaultRegionEndpoint)
        else:
            del kwargs['region']
        kwargs['host'] = region.endpoint
        super(CognitoSyncConnection, self).__init__(**kwargs)
        self.region = region

    def _required_auth_capability(self):
        return ['hmac-v4']

    def delete_dataset(self, identity_pool_id, identity_id, dataset_name):
        """
        Deletes the specific dataset. The dataset will be deleted
        permanently, and the action can't be undone. Datasets that
        this dataset was merged with will no longer report the merge.
        Any consequent operation on this dataset will result in a
        ResourceNotFoundException.

        :type identity_pool_id: string
        :param identity_pool_id: A name-spaced GUID (for example, us-
            east-1:23EC4050-6AEA-7089-A2DD-08002EXAMPLE) created by Amazon
            Cognito. GUID generation is unique within a region.

        :type identity_id: string
        :param identity_id: A name-spaced GUID (for example, us-
            east-1:23EC4050-6AEA-7089-A2DD-08002EXAMPLE) created by Amazon
            Cognito. GUID generation is unique within a region.

        :type dataset_name: string
        :param dataset_name: A string of up to 128 characters. Allowed
            characters are a-z, A-Z, 0-9, '_' (underscore), '-' (dash), and '.'
            (dot).

        """
        uri = '/identitypools/{0}/identities/{1}/datasets/{2}'.format(
            identity_pool_id, identity_id, dataset_name)
        return self.make_request('DELETE', uri, expected_status=200)

    def describe_dataset(self, identity_pool_id, identity_id, dataset_name):
        """
        Gets metadata about a dataset by identity and dataset name.

        :type identity_pool_id: string
        :param identity_pool_id: A name-spaced GUID (for example, us-
            east-1:23EC4050-6AEA-7089-A2DD-08002EXAMPLE) created by Amazon
            Cognito. GUID generation is unique within a region.

        :type identity_id: string
        :param identity_id: A name-spaced GUID (for example, us-
            east-1:23EC4050-6AEA-7089-A2DD-08002EXAMPLE) created by Amazon
            Cognito. GUID generation is unique within a region.

        :type dataset_name: string
        :param dataset_name: A string of up to 128 characters. Allowed
            characters are a-z, A-Z, 0-9, '_' (underscore), '-' (dash), and '.'
            (dot).

        """
        uri = '/identitypools/{0}/identities/{1}/datasets/{2}'.format(
            identity_pool_id, identity_id, dataset_name)
        return self.make_request('GET', uri, expected_status=200)

    def describe_identity_pool_usage(self, identity_pool_id):
        """
        Gets usage details (for example, data storage) about a
        particular identity pool.

        :type identity_pool_id: string
        :param identity_pool_id: A name-spaced GUID (for example, us-
            east-1:23EC4050-6AEA-7089-A2DD-08002EXAMPLE) created by Amazon
            Cognito. GUID generation is unique within a region.

        """
        uri = '/identitypools/{0}'.format(identity_pool_id)
        return self.make_request('GET', uri, expected_status=200)

    def describe_identity_usage(self, identity_pool_id, identity_id):
        """
        Gets usage information for an identity, including number of
        datasets and data usage.

        :type identity_pool_id: string
        :param identity_pool_id: A name-spaced GUID (for example, us-
            east-1:23EC4050-6AEA-7089-A2DD-08002EXAMPLE) created by Amazon
            Cognito. GUID generation is unique within a region.

        :type identity_id: string
        :param identity_id: A name-spaced GUID (for example, us-
            east-1:23EC4050-6AEA-7089-A2DD-08002EXAMPLE) created by Amazon
            Cognito. GUID generation is unique within a region.

        """
        uri = '/identitypools/{0}/identities/{1}'.format(
            identity_pool_id, identity_id)
        return self.make_request('GET', uri, expected_status=200)

    def list_datasets(self, identity_pool_id, identity_id, next_token=None,
                      max_results=None):
        """
        Lists datasets for an identity.

        :type identity_pool_id: string
        :param identity_pool_id: A name-spaced GUID (for example, us-
            east-1:23EC4050-6AEA-7089-A2DD-08002EXAMPLE) created by Amazon
            Cognito. GUID generation is unique within a region.

        :type identity_id: string
        :param identity_id: A name-spaced GUID (for example, us-
            east-1:23EC4050-6AEA-7089-A2DD-08002EXAMPLE) created by Amazon
            Cognito. GUID generation is unique within a region.

        :type next_token: string
        :param next_token: A pagination token for obtaining the next page of
            results.

        :type max_results: integer
        :param max_results: The maximum number of results to be returned.

        """
        uri = '/identitypools/{0}/identities/{1}/datasets'.format(
            identity_pool_id, identity_id)
        params = {}
        headers = {}
        return self.make_request('GET', uri, expected_status=200,
                                 data=json.dumps(params), headers=headers)

    def list_identity_pool_usage(self, next_token=None, max_results=None):
        """
        Gets a list of identity pools registered with Cognito.

        :type next_token: string
        :param next_token: A pagination token for obtaining the next page of
            results.

        :type max_results: integer
        :param max_results: The maximum number of results to be returned.

        """
        uri = '/identitypools'
        params = {}
        headers = {}
        return self.make_request('GET', uri, expected_status=200,
                                 data=json.dumps(params), headers=headers)

    def list_records(self, identity_pool_id, identity_id, dataset_name,
                     last_sync_count=None, next_token=None, max_results=None,
                     sync_session_token=None):
        """
        Gets paginated records, optionally changed after a particular
        sync count for a dataset and identity.

        :type identity_pool_id: string
        :param identity_pool_id: A name-spaced GUID (for example, us-
            east-1:23EC4050-6AEA-7089-A2DD-08002EXAMPLE) created by Amazon
            Cognito. GUID generation is unique within a region.

        :type identity_id: string
        :param identity_id: A name-spaced GUID (for example, us-
            east-1:23EC4050-6AEA-7089-A2DD-08002EXAMPLE) created by Amazon
            Cognito. GUID generation is unique within a region.

        :type dataset_name: string
        :param dataset_name: A string of up to 128 characters. Allowed
            characters are a-z, A-Z, 0-9, '_' (underscore), '-' (dash), and '.'
            (dot).

        :type last_sync_count: long
        :param last_sync_count: The last server sync count for this record.

        :type next_token: string
        :param next_token: A pagination token for obtaining the next page of
            results.

        :type max_results: integer
        :param max_results: The maximum number of results to be returned.

        :type sync_session_token: string
        :param sync_session_token: A token containing a session ID, identity
            ID, and expiration.

        """
        uri = '/identitypools/{0}/identities/{1}/datasets/{2}/records'.format(
            identity_pool_id, identity_id, dataset_name)
        params = {}
        headers = {}
        return self.make_request('GET', uri, expected_status=200,
                                 data=json.dumps(params), headers=headers)

    def update_records(self, identity_pool_id, identity_id, dataset_name,
                       sync_session_token, record_patches=None,
                       client_context=None):
        """
        Posts updates to records and add and delete records for a
        dataset and user.

        :type identity_pool_id: string
        :param identity_pool_id: A name-spaced GUID (for example, us-
            east-1:23EC4050-6AEA-7089-A2DD-08002EXAMPLE) created by Amazon
            Cognito. GUID generation is unique within a region.

        :type identity_id: string
        :param identity_id: A name-spaced GUID (for example, us-
            east-1:23EC4050-6AEA-7089-A2DD-08002EXAMPLE) created by Amazon
            Cognito. GUID generation is unique within a region.

        :type dataset_name: string
        :param dataset_name: A string of up to 128 characters. Allowed
            characters are a-z, A-Z, 0-9, '_' (underscore), '-' (dash), and '.'
            (dot).

        :type record_patches: list
        :param record_patches:

        :type sync_session_token: string
        :param sync_session_token: The SyncSessionToken returned by a previous
            call to ListRecords for this dataset and identity.

        :type client_context: string
        :param client_context:

        """
        uri = '/identitypools/{0}/identities/{1}/datasets/{2}'.format(
            identity_pool_id, identity_id, dataset_name)
        params = {'SyncSessionToken': sync_session_token, }
        headers = {}
        if record_patches is not None:
            params['RecordPatches'] = record_patches
        if client_context is not None:
            headers['x-amz-Client-Context'] = client_context
        return self.make_request('POST', uri, expected_status=200,
                                 data=json.dumps(params), headers=headers)

    def make_request(self, verb, resource, headers=None, data='',
                     expected_status=None, params=None):
        if headers is None:
            headers = {}
        response = AWSAuthConnection.make_request(
            self, verb, resource, headers=headers, data=data, params=params)
        body = json.loads(response.read().decode('utf-8'))
        if response.status == expected_status:
            return body
        else:
            error_type = response.getheader('x-amzn-ErrorType').split(':')[0]
            error_class = self._faults.get(error_type, self.ResponseError)
            raise error_class(response.status, response.reason, body)

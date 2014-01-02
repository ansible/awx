# -*- coding: utf-8 -*-
# Copyright (c) 2012 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2012 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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

import os

import boto.glacier
from boto.compat import json
from boto.connection import AWSAuthConnection
from .exceptions import UnexpectedHTTPResponseError
from .response import GlacierResponse
from .utils import ResettingFileSender


class Layer1(AWSAuthConnection):

    Version = '2012-06-01'
    """Glacier API version."""

    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None,
                 account_id='-', is_secure=True, port=None,
                 proxy=None, proxy_port=None,
                 proxy_user=None, proxy_pass=None, debug=0,
                 https_connection_factory=None, path='/',
                 provider='aws', security_token=None,
                 suppress_consec_slashes=True,
                 region=None, region_name='us-east-1'):

        if not region:
            for reg in boto.glacier.regions():
                if reg.name == region_name:
                    region = reg
                    break

        self.region = region
        self.account_id = account_id
        super(Layer1, self).__init__(region.endpoint,
                                   aws_access_key_id, aws_secret_access_key,
                                   is_secure, port, proxy, proxy_port,
                                   proxy_user, proxy_pass, debug,
                                   https_connection_factory,
                                   path, provider, security_token,
                                   suppress_consec_slashes)

    def _required_auth_capability(self):
        return ['hmac-v4']

    def make_request(self, verb, resource, headers=None,
                     data='', ok_responses=(200,), params=None,
                     sender=None, response_headers=None):
        if headers is None:
            headers = {}
        headers['x-amz-glacier-version'] = self.Version
        uri = '/%s/%s' % (self.account_id, resource)
        response = super(Layer1, self).make_request(verb, uri,
                                                  params=params,
                                                  headers=headers,
                                                  sender=sender,
                                                  data=data)
        if response.status in ok_responses:
            return GlacierResponse(response, response_headers)
        else:
            # create glacier-specific exceptions
            raise UnexpectedHTTPResponseError(ok_responses, response)

    # Vaults

    def list_vaults(self, limit=None, marker=None):
        """
        This operation lists all vaults owned by the calling user’s
        account. The list returned in the response is ASCII-sorted by
        vault name.

        By default, this operation returns up to 1,000 items. If there
        are more vaults to list, the marker field in the response body
        contains the vault Amazon Resource Name (ARN) at which to
        continue the list with a new List Vaults request; otherwise,
        the marker field is null. In your next List Vaults request you
        set the marker parameter to the value Amazon Glacier returned
        in the responses to your previous List Vaults request. You can
        also limit the number of vaults returned in the response by
        specifying the limit parameter in the request.

        :type limit: int
        :param limit: The maximum number of items returned in the
            response. If you don't specify a value, the List Vaults
            operation returns up to 1,000 items.

        :type marker: str
        :param marker: A string used for pagination. marker specifies
            the vault ARN after which the listing of vaults should
            begin. (The vault specified by marker is not included in
            the returned list.) Get the marker value from a previous
            List Vaults response. You need to include the marker only
            if you are continuing the pagination of results started in
            a previous List Vaults request. Specifying an empty value
            ("") for the marker returns a list of vaults starting
            from the first vault.
        """
        params = {}
        if limit:
            params['limit'] = limit
        if marker:
            params['marker'] = marker
        return self.make_request('GET', 'vaults', params=params)

    def describe_vault(self, vault_name):
        """
        This operation returns information about a vault, including
        the vault Amazon Resource Name (ARN), the date the vault was
        created, the number of archives contained within the vault,
        and the total size of all the archives in the vault. The
        number of archives and their total size are as of the last
        vault inventory Amazon Glacier generated.  Amazon Glacier
        generates vault inventories approximately daily. This means
        that if you add or remove an archive from a vault, and then
        immediately send a Describe Vault request, the response might
        not reflect the changes.

        :type vault_name: str
        :param vault_name: The name of the new vault
        """
        uri = 'vaults/%s' % vault_name
        return self.make_request('GET', uri)

    def create_vault(self, vault_name):
        """
        This operation creates a new vault with the specified name.
        The name of the vault must be unique within a region for an
        AWS account. You can create up to 1,000 vaults per
        account. For information on creating more vaults, go to the
        Amazon Glacier product detail page.

        You must use the following guidelines when naming a vault.

        Names can be between 1 and 255 characters long.

        Allowed characters are a–z, A–Z, 0–9, '_' (underscore),
        '-' (hyphen), and '.' (period).

        This operation is idempotent, you can send the same request
        multiple times and it has no further effect after the first
        time Amazon Glacier creates the specified vault.

        :type vault_name: str
        :param vault_name: The name of the new vault
        """
        uri = 'vaults/%s' % vault_name
        return self.make_request('PUT', uri, ok_responses=(201,),
                                 response_headers=[('Location', 'Location')])

    def delete_vault(self, vault_name):
        """
        This operation deletes a vault. Amazon Glacier will delete a
        vault only if there are no archives in the vault as per the
        last inventory and there have been no writes to the vault
        since the last inventory. If either of these conditions is not
        satisfied, the vault deletion fails (that is, the vault is not
        removed) and Amazon Glacier returns an error.

        This operation is idempotent, you can send the same request
        multiple times and it has no further effect after the first
        time Amazon Glacier delete the specified vault.

        :type vault_name: str
        :param vault_name: The name of the new vault
        """
        uri = 'vaults/%s' % vault_name
        return self.make_request('DELETE', uri, ok_responses=(204,))

    def get_vault_notifications(self, vault_name):
        """
        This operation retrieves the notification-configuration
        subresource set on the vault.

        :type vault_name: str
        :param vault_name: The name of the new vault
        """
        uri = 'vaults/%s/notification-configuration' % vault_name
        return self.make_request('GET', uri)

    def set_vault_notifications(self, vault_name, notification_config):
        """
        This operation retrieves the notification-configuration
        subresource set on the vault.

        :type vault_name: str
        :param vault_name: The name of the new vault

        :type notification_config: dict
        :param notification_config: A Python dictionary containing
            an SNS Topic and events for which you want Amazon Glacier
            to send notifications to the topic.  Possible events are:

            * ArchiveRetrievalCompleted - occurs when a job that was
              initiated for an archive retrieval is completed.
            * InventoryRetrievalCompleted - occurs when a job that was
              initiated for an inventory retrieval is completed.

            The format of the dictionary is:

                {'SNSTopic': 'mytopic',
                 'Events': [event1,...]}
        """
        uri = 'vaults/%s/notification-configuration' % vault_name
        json_config = json.dumps(notification_config)
        return self.make_request('PUT', uri, data=json_config,
                                 ok_responses=(204,))

    def delete_vault_notifications(self, vault_name):
        """
        This operation deletes the notification-configuration
        subresource set on the vault.

        :type vault_name: str
        :param vault_name: The name of the new vault
        """
        uri = 'vaults/%s/notification-configuration' % vault_name
        return self.make_request('DELETE', uri, ok_responses=(204,))

    # Jobs

    def list_jobs(self, vault_name, completed=None, status_code=None,
                  limit=None, marker=None):
        """
        This operation lists jobs for a vault including jobs that are
        in-progress and jobs that have recently finished.

        :type vault_name: str
        :param vault_name: The name of the vault.

        :type completed: boolean
        :param completed: Specifies the state of the jobs to return.
            If a value of True is passed, only completed jobs will
            be returned.  If a value of False is passed, only
            uncompleted jobs will be returned.  If no value is
            passed, all jobs will be returned.

        :type status_code: string
        :param status_code: Specifies the type of job status to return.
            Valid values are: InProgress|Succeeded|Failed.  If not
            specified, jobs with all status codes are returned.

        :type limit: int
        :param limit: The maximum number of items returned in the
            response. If you don't specify a value, the List Jobs
            operation returns up to 1,000 items.

        :type marker: str
        :param marker: An opaque string used for pagination. marker
            specifies the job at which the listing of jobs should
            begin. Get the marker value from a previous List Jobs
            response. You need only include the marker if you are
            continuing the pagination of results started in a previous
            List Jobs request.

        """
        params = {}
        if limit:
            params['limit'] = limit
        if marker:
            params['marker'] = marker
        if status_code:
            params['statuscode'] = status_code
        if completed is not None:
            params['completed'] = 'true' if completed else 'false'
        uri = 'vaults/%s/jobs' % vault_name
        return self.make_request('GET', uri, params=params)

    def describe_job(self, vault_name, job_id):
        """
        This operation returns information about a job you previously
        initiated, including the job initiation date, the user who
        initiated the job, the job status code/message and the Amazon
        Simple Notification Service (Amazon SNS) topic to notify after
        Amazon Glacier completes the job.

        :type vault_name: str
        :param vault_name: The name of the new vault

        :type job_id: str
        :param job_id: The ID of the job.
        """
        uri = 'vaults/%s/jobs/%s' % (vault_name, job_id)
        return self.make_request('GET', uri, ok_responses=(200,))

    def initiate_job(self, vault_name, job_data):
        """
        This operation initiates a job of the specified
        type. Retrieving an archive or a vault inventory are
        asynchronous operations that require you to initiate a job. It
        is a two-step process:

        * Initiate a retrieval job.
        * After the job completes, download the bytes.

        The retrieval is executed asynchronously.  When you initiate
        a retrieval job, Amazon Glacier creates a job and returns a
        job ID in the response.

        :type vault_name: str
        :param vault_name: The name of the new vault

        :type job_data: dict
        :param job_data: A Python dictionary containing the
            information about the requested job.  The dictionary
            can contain the following attributes:

            * ArchiveId - The ID of the archive you want to retrieve.
              This field is required only if the Type is set to
              archive-retrieval.
            * Description - The optional description for the job.
            * Format - When initiating a job to retrieve a vault
              inventory, you can optionally add this parameter to
              specify the output format.  Valid values are: CSV|JSON.
            * SNSTopic - The Amazon SNS topic ARN where Amazon Glacier
              sends a notification when the job is completed and the
              output is ready for you to download.
            * Type - The job type.  Valid values are:
              archive-retrieval|inventory-retrieval
            * RetrievalByteRange - Optionally specify the range of
              bytes to retrieve.

        """
        uri = 'vaults/%s/jobs' % vault_name
        response_headers = [('x-amz-job-id', u'JobId'),
                            ('Location', u'Location')]
        json_job_data = json.dumps(job_data)
        return self.make_request('POST', uri, data=json_job_data,
                                 ok_responses=(202,),
                                 response_headers=response_headers)

    def get_job_output(self, vault_name, job_id, byte_range=None):
        """
        This operation downloads the output of the job you initiated
        using Initiate a Job. Depending on the job type
        you specified when you initiated the job, the output will be
        either the content of an archive or a vault inventory.

        You can download all the job output or download a portion of
        the output by specifying a byte range. In the case of an
        archive retrieval job, depending on the byte range you
        specify, Amazon Glacier returns the checksum for the portion
        of the data. You can compute the checksum on the client and
        verify that the values match to ensure the portion you
        downloaded is the correct data.

        :type vault_name: str :param
        :param vault_name: The name of the new vault

        :type job_id: str
        :param job_id: The ID of the job.

        :type byte_range: tuple
        :param range: A tuple of integers specifying the slice (in bytes)
            of the archive you want to receive
        """
        response_headers = [('x-amz-sha256-tree-hash', u'TreeHash'),
                            ('Content-Range', u'ContentRange'),
                            ('Content-Type', u'ContentType')]
        headers = None
        if byte_range:
            headers = {'Range': 'bytes=%d-%d' % byte_range}
        uri = 'vaults/%s/jobs/%s/output' % (vault_name, job_id)
        response = self.make_request('GET', uri, headers=headers,
                                     ok_responses=(200, 206),
                                     response_headers=response_headers)
        return response

    # Archives

    def upload_archive(self, vault_name, archive,
                       linear_hash, tree_hash, description=None):
        """
        This operation adds an archive to a vault. For a successful
        upload, your data is durably persisted. In response, Amazon
        Glacier returns the archive ID in the x-amz-archive-id header
        of the response. You should save the archive ID returned so
        that you can access the archive later.

        :type vault_name: str :param
        :param vault_name: The name of the vault

        :type archive: bytes
        :param archive: The data to upload.

        :type linear_hash: str
        :param linear_hash: The SHA256 checksum (a linear hash) of the
            payload.

        :type tree_hash: str
        :param tree_hash: The user-computed SHA256 tree hash of the
            payload.  For more information on computing the
            tree hash, see http://goo.gl/u7chF.

        :type description: str
        :param description: An optional description of the archive.
        """
        response_headers = [('x-amz-archive-id', u'ArchiveId'),
                            ('Location', u'Location'),
                            ('x-amz-sha256-tree-hash', u'TreeHash')]
        uri = 'vaults/%s/archives' % vault_name
        try:
            content_length = str(len(archive))
        except (TypeError, AttributeError):
            # If a file like object is provided, try to retrieve
            # the file size via fstat.
            content_length = str(os.fstat(archive.fileno()).st_size)
        headers = {'x-amz-content-sha256': linear_hash,
                   'x-amz-sha256-tree-hash': tree_hash,
                   'Content-Length': content_length}
        if description:
            headers['x-amz-archive-description'] = description
        if self._is_file_like(archive):
            sender = ResettingFileSender(archive)
        else:
            sender = None
        return self.make_request('POST', uri, headers=headers,
                                sender=sender,
                                data=archive, ok_responses=(201,),
                                response_headers=response_headers)

    def _is_file_like(self, archive):
        return hasattr(archive, 'seek') and hasattr(archive, 'tell')

    def delete_archive(self, vault_name, archive_id):
        """
        This operation deletes an archive from a vault.

        :type vault_name: str
        :param vault_name: The name of the new vault

        :type archive_id: str
        :param archive_id: The ID for the archive to be deleted.
        """
        uri = 'vaults/%s/archives/%s' % (vault_name, archive_id)
        return self.make_request('DELETE', uri, ok_responses=(204,))

    # Multipart

    def initiate_multipart_upload(self, vault_name, part_size,
                                  description=None):
        """
        Initiate a multipart upload.  Amazon Glacier creates a
        multipart upload resource and returns it's ID.  You use this
        ID in subsequent multipart upload operations.

        :type vault_name: str
        :param vault_name: The name of the vault.

        :type description: str
        :param description: An optional description of the archive.

        :type part_size: int
        :param part_size: The size of each part except the last, in bytes.
            The part size must be a multiple of 1024 KB multiplied by
            a power of 2.  The minimum allowable part size is 1MB and the
            maximum is 4GB.
        """
        response_headers = [('x-amz-multipart-upload-id', u'UploadId'),
                            ('Location', u'Location')]
        headers = {'x-amz-part-size': str(part_size)}
        if description:
            headers['x-amz-archive-description'] = description
        uri = 'vaults/%s/multipart-uploads' % vault_name
        response = self.make_request('POST', uri, headers=headers,
                                     ok_responses=(201,),
                                     response_headers=response_headers)
        return response

    def complete_multipart_upload(self, vault_name, upload_id,
                                  sha256_treehash, archive_size):
        """
        Call this to inform Amazon Glacier that all of the archive parts
        have been uploaded and Amazon Glacier can now assemble the archive
        from the uploaded parts.

        :type vault_name: str
        :param vault_name: The name of the vault.

        :type upload_id: str
        :param upload_id: The unique ID associated with this upload
            operation.

        :type sha256_treehash: str
        :param sha256_treehash: The SHA256 tree hash of the entire
            archive. It is the tree hash of SHA256 tree hash of the
            individual parts. If the value you specify in the request
            does not match the SHA256 tree hash of the final assembled
            archive as computed by Amazon Glacier, Amazon Glacier
            returns an error and the request fails.

        :type archive_size: int
        :param archive_size: The total size, in bytes, of the entire
            archive. This value should be the sum of all the sizes of
            the individual parts that you uploaded.
        """
        response_headers = [('x-amz-archive-id', u'ArchiveId'),
                            ('Location', u'Location')]
        headers = {'x-amz-sha256-tree-hash': sha256_treehash,
                   'x-amz-archive-size': str(archive_size)}
        uri = 'vaults/%s/multipart-uploads/%s' % (vault_name, upload_id)
        response = self.make_request('POST', uri, headers=headers,
                                     ok_responses=(201,),
                                     response_headers=response_headers)
        return response

    def abort_multipart_upload(self, vault_name, upload_id):
        """
        Call this to abort a multipart upload identified by the upload ID.

        :type vault_name: str
        :param vault_name: The name of the vault.

        :type upload_id: str
        :param upload_id: The unique ID associated with this upload
            operation.
        """
        uri = 'vaults/%s/multipart-uploads/%s' % (vault_name, upload_id)
        return self.make_request('DELETE', uri, ok_responses=(204,))

    def list_multipart_uploads(self, vault_name, limit=None, marker=None):
        """
        Lists in-progress multipart uploads for the specified vault.

        :type vault_name: str
        :param vault_name: The name of the vault.

        :type limit: int
        :param limit: The maximum number of items returned in the
            response. If you don't specify a value, the operation
            returns up to 1,000 items.

        :type marker: str
        :param marker: An opaque string used for pagination. marker
            specifies the item at which the listing should
            begin. Get the marker value from a previous
            response. You need only include the marker if you are
            continuing the pagination of results started in a previous
            request.
        """
        params = {}
        if limit:
            params['limit'] = limit
        if marker:
            params['marker'] = marker
        uri = 'vaults/%s/multipart-uploads' % vault_name
        return self.make_request('GET', uri, params=params)

    def list_parts(self, vault_name, upload_id, limit=None, marker=None):
        """
        Lists in-progress multipart uploads for the specified vault.

        :type vault_name: str
        :param vault_name: The name of the vault.

        :type upload_id: str
        :param upload_id: The unique ID associated with this upload
            operation.

        :type limit: int
        :param limit: The maximum number of items returned in the
            response. If you don't specify a value, the operation
            returns up to 1,000 items.

        :type marker: str
        :param marker: An opaque string used for pagination. marker
            specifies the item at which the listing should
            begin. Get the marker value from a previous
            response. You need only include the marker if you are
            continuing the pagination of results started in a previous
            request.
        """
        params = {}
        if limit:
            params['limit'] = limit
        if marker:
            params['marker'] = marker
        uri = 'vaults/%s/multipart-uploads/%s' % (vault_name, upload_id)
        return self.make_request('GET', uri, params=params)

    def upload_part(self, vault_name, upload_id, linear_hash,
                    tree_hash, byte_range, part_data):
        """
        Lists in-progress multipart uploads for the specified vault.

        :type vault_name: str
        :param vault_name: The name of the vault.

        :type linear_hash: str
        :param linear_hash: The SHA256 checksum (a linear hash) of the
            payload.

        :type tree_hash: str
        :param tree_hash: The user-computed SHA256 tree hash of the
            payload.  For more information on computing the
            tree hash, see http://goo.gl/u7chF.

        :type upload_id: str
        :param upload_id: The unique ID associated with this upload
            operation.

        :type byte_range: tuple of ints
        :param byte_range: Identfies the range of bytes in the assembled
            archive that will be uploaded in this part.

        :type part_data: bytes
        :param part_data: The data to be uploaded for the part
        """
        headers = {'x-amz-content-sha256': linear_hash,
                   'x-amz-sha256-tree-hash': tree_hash,
                   'Content-Range': 'bytes %d-%d/*' % byte_range}
        response_headers = [('x-amz-sha256-tree-hash', u'TreeHash')]
        uri = 'vaults/%s/multipart-uploads/%s' % (vault_name, upload_id)
        return self.make_request('PUT', uri, headers=headers,
                                 data=part_data, ok_responses=(204,),
                                 response_headers=response_headers)

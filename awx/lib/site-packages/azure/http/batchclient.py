#-------------------------------------------------------------------------
# Copyright (c) Microsoft.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#--------------------------------------------------------------------------
import sys
import uuid

from azure import (
    _update_request_uri_query,
    WindowsAzureError,
    WindowsAzureBatchOperationError,
    _get_children_from_path,
    url_unquote,
    _ERROR_CANNOT_FIND_PARTITION_KEY,
    _ERROR_CANNOT_FIND_ROW_KEY,
    _ERROR_INCORRECT_TABLE_IN_BATCH,
    _ERROR_INCORRECT_PARTITION_KEY_IN_BATCH,
    _ERROR_DUPLICATE_ROW_KEY_IN_BATCH,
    _ERROR_BATCH_COMMIT_FAIL,
    )
from azure.http import HTTPError, HTTPRequest, HTTPResponse
from azure.http.httpclient import _HTTPClient
from azure.storage import (
    _update_storage_table_header,
    METADATA_NS,
    _sign_storage_table_request,
    )
from xml.dom import minidom

_DATASERVICES_NS = 'http://schemas.microsoft.com/ado/2007/08/dataservices'

if sys.version_info < (3,):
    def _new_boundary():
        return str(uuid.uuid1())
else:
    def _new_boundary():
        return str(uuid.uuid1()).encode('utf-8')


class _BatchClient(_HTTPClient):

    '''
    This is the class that is used for batch operation for storage table
    service. It only supports one changeset.
    '''

    def __init__(self, service_instance, account_key, account_name,
                 protocol='http'):
        _HTTPClient.__init__(self, service_instance, account_name=account_name,
                             account_key=account_key, protocol=protocol)
        self.is_batch = False
        self.batch_requests = []
        self.batch_table = ''
        self.batch_partition_key = ''
        self.batch_row_keys = []

    def get_request_table(self, request):
        '''
        Extracts table name from request.uri. The request.uri has either
        "/mytable(...)" or "/mytable" format.

        request: the request to insert, update or delete entity
        '''
        if '(' in request.path:
            pos = request.path.find('(')
            return request.path[1:pos]
        else:
            return request.path[1:]

    def get_request_partition_key(self, request):
        '''
        Extracts PartitionKey from request.body if it is a POST request or from
        request.path if it is not a POST request. Only insert operation request
        is a POST request and the PartitionKey is in the request body.

        request: the request to insert, update or delete entity
        '''
        if request.method == 'POST':
            doc = minidom.parseString(request.body)
            part_key = _get_children_from_path(
                doc, 'entry', 'content', (METADATA_NS, 'properties'),
                (_DATASERVICES_NS, 'PartitionKey'))
            if not part_key:
                raise WindowsAzureError(_ERROR_CANNOT_FIND_PARTITION_KEY)
            return part_key[0].firstChild.nodeValue
        else:
            uri = url_unquote(request.path)
            pos1 = uri.find('PartitionKey=\'')
            pos2 = uri.find('\',', pos1)
            if pos1 == -1 or pos2 == -1:
                raise WindowsAzureError(_ERROR_CANNOT_FIND_PARTITION_KEY)
            return uri[pos1 + len('PartitionKey=\''):pos2]

    def get_request_row_key(self, request):
        '''
        Extracts RowKey from request.body if it is a POST request or from
        request.path if it is not a POST request. Only insert operation request
        is a POST request and the Rowkey is in the request body.

        request: the request to insert, update or delete entity
        '''
        if request.method == 'POST':
            doc = minidom.parseString(request.body)
            row_key = _get_children_from_path(
                doc, 'entry', 'content', (METADATA_NS, 'properties'),
                (_DATASERVICES_NS, 'RowKey'))
            if not row_key:
                raise WindowsAzureError(_ERROR_CANNOT_FIND_ROW_KEY)
            return row_key[0].firstChild.nodeValue
        else:
            uri = url_unquote(request.path)
            pos1 = uri.find('RowKey=\'')
            pos2 = uri.find('\')', pos1)
            if pos1 == -1 or pos2 == -1:
                raise WindowsAzureError(_ERROR_CANNOT_FIND_ROW_KEY)
            row_key = uri[pos1 + len('RowKey=\''):pos2]
            return row_key

    def validate_request_table(self, request):
        '''
        Validates that all requests have the same table name. Set the table
        name if it is the first request for the batch operation.

        request: the request to insert, update or delete entity
        '''
        if self.batch_table:
            if self.get_request_table(request) != self.batch_table:
                raise WindowsAzureError(_ERROR_INCORRECT_TABLE_IN_BATCH)
        else:
            self.batch_table = self.get_request_table(request)

    def validate_request_partition_key(self, request):
        '''
        Validates that all requests have the same PartitiionKey. Set the
        PartitionKey if it is the first request for the batch operation.

        request: the request to insert, update or delete entity
        '''
        if self.batch_partition_key:
            if self.get_request_partition_key(request) != \
                self.batch_partition_key:
                raise WindowsAzureError(_ERROR_INCORRECT_PARTITION_KEY_IN_BATCH)
        else:
            self.batch_partition_key = self.get_request_partition_key(request)

    def validate_request_row_key(self, request):
        '''
        Validates that all requests have the different RowKey and adds RowKey
        to existing RowKey list.

        request: the request to insert, update or delete entity
        '''
        if self.batch_row_keys:
            if self.get_request_row_key(request) in self.batch_row_keys:
                raise WindowsAzureError(_ERROR_DUPLICATE_ROW_KEY_IN_BATCH)
        else:
            self.batch_row_keys.append(self.get_request_row_key(request))

    def begin_batch(self):
        '''
        Starts the batch operation. Intializes the batch variables

        is_batch: batch operation flag.
        batch_table: the table name of the batch operation
        batch_partition_key: the PartitionKey of the batch requests.
        batch_row_keys: the RowKey list of adding requests.
        batch_requests: the list of the requests.
        '''
        self.is_batch = True
        self.batch_table = ''
        self.batch_partition_key = ''
        self.batch_row_keys = []
        self.batch_requests = []

    def insert_request_to_batch(self, request):
        '''
        Adds request to batch operation.

        request: the request to insert, update or delete entity
        '''
        self.validate_request_table(request)
        self.validate_request_partition_key(request)
        self.validate_request_row_key(request)
        self.batch_requests.append(request)

    def commit_batch(self):
        ''' Resets batch flag and commits the batch requests. '''
        if self.is_batch:
            self.is_batch = False
            self.commit_batch_requests()

    def commit_batch_requests(self):
        ''' Commits the batch requests. '''

        batch_boundary = b'batch_' + _new_boundary()
        changeset_boundary = b'changeset_' + _new_boundary()

        # Commits batch only the requests list is not empty.
        if self.batch_requests:
            request = HTTPRequest()
            request.method = 'POST'
            request.host = self.batch_requests[0].host
            request.path = '/$batch'
            request.headers = [
                ('Content-Type', 'multipart/mixed; boundary=' + \
                    batch_boundary.decode('utf-8')),
                ('Accept', 'application/atom+xml,application/xml'),
                ('Accept-Charset', 'UTF-8')]

            request.body = b'--' + batch_boundary + b'\n'
            request.body += b'Content-Type: multipart/mixed; boundary='
            request.body += changeset_boundary + b'\n\n'

            content_id = 1

            # Adds each request body to the POST data.
            for batch_request in self.batch_requests:
                request.body += b'--' + changeset_boundary + b'\n'
                request.body += b'Content-Type: application/http\n'
                request.body += b'Content-Transfer-Encoding: binary\n\n'
                request.body += batch_request.method.encode('utf-8')
                request.body += b' http://'
                request.body += batch_request.host.encode('utf-8')
                request.body += batch_request.path.encode('utf-8')
                request.body += b' HTTP/1.1\n'
                request.body += b'Content-ID: '
                request.body += str(content_id).encode('utf-8') + b'\n'
                content_id += 1

                # Add different headers for different type requests.
                if not batch_request.method == 'DELETE':
                    request.body += \
                        b'Content-Type: application/atom+xml;type=entry\n'
                    for name, value in batch_request.headers:
                        if name == 'If-Match':
                            request.body += name.encode('utf-8') + b': '
                            request.body += value.encode('utf-8') + b'\n'
                            break
                    request.body += b'Content-Length: '
                    request.body += str(len(batch_request.body)).encode('utf-8')
                    request.body += b'\n\n'
                    request.body += batch_request.body + b'\n'
                else:
                    for name, value in batch_request.headers:
                        # If-Match should be already included in
                        # batch_request.headers, but in case it is missing,
                        # just add it.
                        if name == 'If-Match':
                            request.body += name.encode('utf-8') + b': '
                            request.body += value.encode('utf-8') + b'\n\n'
                            break
                    else:
                        request.body += b'If-Match: *\n\n'

            request.body += b'--' + changeset_boundary + b'--' + b'\n'
            request.body += b'--' + batch_boundary + b'--'

            request.path, request.query = _update_request_uri_query(request)
            request.headers = _update_storage_table_header(request)
            auth = _sign_storage_table_request(request,
                                               self.account_name,
                                               self.account_key)
            request.headers.append(('Authorization', auth))

            # Submit the whole request as batch request.
            response = self.perform_request(request)
            if response.status >= 300:
                raise HTTPError(response.status,
                                _ERROR_BATCH_COMMIT_FAIL,
                                self.respheader,
                                response.body)

            # http://www.odata.org/documentation/odata-version-2-0/batch-processing/
            # The body of a ChangeSet response is either a response for all the
            # successfully processed change request within the ChangeSet,
            # formatted exactly as it would have appeared outside of a batch, 
            # or a single response indicating a failure of the entire ChangeSet.
            responses = self._parse_batch_response(response.body)
            if responses and responses[0].status >= 300:
                self._report_batch_error(responses[0])

    def cancel_batch(self):
        ''' Resets the batch flag. '''
        self.is_batch = False

    def _parse_batch_response(self, body):
        parts = body.split(b'--changesetresponse_')

        responses = []
        for part in parts:
            httpLocation = part.find(b'HTTP/')
            if httpLocation > 0:
                response = self._parse_batch_response_part(part[httpLocation:])
                responses.append(response)

        return responses

    def _parse_batch_response_part(self, part):
        lines = part.splitlines();

        # First line is the HTTP status/reason
        status, _, reason = lines[0].partition(b' ')[2].partition(b' ')

        # Followed by headers and body
        headers = []
        body = b''
        isBody = False
        for line in lines[1:]:
            if line == b'' and not isBody:
                isBody = True
            elif isBody:
                body += line
            else:
                headerName, _, headerVal = line.partition(b':')
                headers.append((headerName.lower(), headerVal))

        return HTTPResponse(int(status), reason.strip(), headers, body)

    def _report_batch_error(self, response):
        xml = response.body.decode('utf-8')
        doc = minidom.parseString(xml)

        n = _get_children_from_path(doc, (METADATA_NS, 'error'), 'code')
        code = n[0].firstChild.nodeValue if n and n[0].firstChild else ''

        n = _get_children_from_path(doc, (METADATA_NS, 'error'), 'message')
        message = n[0].firstChild.nodeValue if n and n[0].firstChild else xml

        raise WindowsAzureBatchOperationError(message, code)

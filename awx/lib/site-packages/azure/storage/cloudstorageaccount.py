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
from azure.storage.blobservice import BlobService
from azure.storage.tableservice import TableService
from azure.storage.queueservice import QueueService


class CloudStorageAccount(object):

    """
    Provides a factory for creating the blob, queue, and table services
    with a common account name and account key.  Users can either use the
    factory or can construct the appropriate service directly.
    """

    def __init__(self, account_name=None, account_key=None):
        self.account_name = account_name
        self.account_key = account_key

    def create_blob_service(self):
        return BlobService(self.account_name, self.account_key)

    def create_table_service(self):
        return TableService(self.account_name, self.account_key)

    def create_queue_service(self):
        return QueueService(self.account_name, self.account_key)

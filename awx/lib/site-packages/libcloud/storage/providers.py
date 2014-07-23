# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from libcloud.utils.misc import get_driver as get_provider_driver
from libcloud.utils.misc import set_driver as set_provider_driver
from libcloud.storage.types import Provider

DRIVERS = {
    Provider.DUMMY:
    ('libcloud.storage.drivers.dummy', 'DummyStorageDriver'),
    Provider.CLOUDFILES:
    ('libcloud.storage.drivers.cloudfiles', 'CloudFilesStorageDriver'),
    Provider.OPENSTACK_SWIFT:
    ('libcloud.storage.drivers.cloudfiles', 'OpenStackSwiftStorageDriver'),
    Provider.S3:
    ('libcloud.storage.drivers.s3', 'S3StorageDriver'),
    Provider.S3_US_WEST:
    ('libcloud.storage.drivers.s3', 'S3USWestStorageDriver'),
    Provider.S3_US_WEST_OREGON:
    ('libcloud.storage.drivers.s3', 'S3USWestOregonStorageDriver'),
    Provider.S3_EU_WEST:
    ('libcloud.storage.drivers.s3', 'S3EUWestStorageDriver'),
    Provider.S3_AP_SOUTHEAST:
    ('libcloud.storage.drivers.s3', 'S3APSEStorageDriver'),
    Provider.S3_AP_NORTHEAST:
    ('libcloud.storage.drivers.s3', 'S3APNEStorageDriver'),
    Provider.NINEFOLD:
    ('libcloud.storage.drivers.ninefold', 'NinefoldStorageDriver'),
    Provider.GOOGLE_STORAGE:
    ('libcloud.storage.drivers.google_storage', 'GoogleStorageDriver'),
    Provider.NIMBUS:
    ('libcloud.storage.drivers.nimbus', 'NimbusStorageDriver'),
    Provider.LOCAL:
    ('libcloud.storage.drivers.local', 'LocalStorageDriver'),
    Provider.AZURE_BLOBS:
    ('libcloud.storage.drivers.azure_blobs', 'AzureBlobsStorageDriver'),
    Provider.KTUCLOUD:
    ('libcloud.storage.drivers.ktucloud', 'KTUCloudStorageDriver'),

    # Deprecated
    Provider.CLOUDFILES_US:
    ('libcloud.storage.drivers.cloudfiles', 'CloudFilesUSStorageDriver'),
    Provider.CLOUDFILES_UK:
    ('libcloud.storage.drivers.cloudfiles', 'CloudFilesUKStorageDriver'),
    Provider.CLOUDFILES_SWIFT:
    ('libcloud.storage.drivers.cloudfiles', 'OpenStackSwiftStorageDriver')
}


def get_driver(provider):
    return get_provider_driver(DRIVERS, provider)


def set_driver(provider, module, klass):
    return set_provider_driver(DRIVERS, provider, module, klass)

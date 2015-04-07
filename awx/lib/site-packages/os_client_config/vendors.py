# flake8: noqa
# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

CLOUD_DEFAULTS = dict(
    hp=dict(
        auth=dict(
            auth_url='https://region-b.geo-1.identity.hpcloudsvc.com:35357/v2.0',
        ),
        region_name='region-b.geo-1',
        dns_service_type='hpext:dns',
        image_api_version='1',
    ),
    rackspace=dict(
        auth=dict(
            auth_url='https://identity.api.rackspacecloud.com/v2.0/',
        ),
        database_service_type='rax:database',
        compute_service_name='cloudServersOpenStack',
        image_api_version='2',
    )
)

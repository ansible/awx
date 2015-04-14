# Copyright 2013 Mirantis Inc.
# All Rights Reserved
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
# @author: Eugene Nikanorov, Mirantis Inc.
#

import sys

from neutronclient.neutron.v2_0 import servicetype
from neutronclient.tests.unit import test_cli20


class CLITestV20ServiceProvidersJSON(test_cli20.CLITestV20Base):
    id_field = "name"

    def setUp(self):
        super(CLITestV20ServiceProvidersJSON, self).setUp(
            plurals={'tags': 'tag'}
        )

    def test_list_service_providers(self):
        resources = "service_providers"
        cmd = servicetype.ListServiceProvider(test_cli20.MyApp(sys.stdout),
                                              None)
        self._test_list_resources(resources, cmd, True)

    def test_list_service_providers_pagination(self):
        resources = "service_providers"
        cmd = servicetype.ListServiceProvider(test_cli20.MyApp(sys.stdout),
                                              None)
        self._test_list_resources_with_pagination(resources, cmd)

    def test_list_service_providers_sort(self):
        resources = "service_providers"
        cmd = servicetype.ListServiceProvider(test_cli20.MyApp(sys.stdout),
                                              None)
        self._test_list_resources(resources, cmd,
                                  sort_key=["name"],
                                  sort_dir=["asc", "desc"])

    def test_list_service_providers_limit(self):
        resources = "service_providers"
        cmd = servicetype.ListServiceProvider(test_cli20.MyApp(sys.stdout),
                                              None)
        self._test_list_resources(resources, cmd, page_size=1000)


class CLITestV20ServiceProvidersXML(CLITestV20ServiceProvidersJSON):
    format = 'xml'

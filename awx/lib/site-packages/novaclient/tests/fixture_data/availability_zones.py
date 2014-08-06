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

import httpretty

from novaclient.openstack.common import jsonutils
from novaclient.tests.fixture_data import base


class V1(base.Fixture):

    base_url = 'os-availability-zone'

    zone_info_key = 'availabilityZoneInfo'
    zone_name_key = 'zoneName'
    zone_state_key = 'zoneState'

    def setUp(self):
        super(V1, self).setUp()

        get_os_availability_zone = {
            self.zone_info_key: [
                {
                    self.zone_name_key: "zone-1",
                    self.zone_state_key: {"available": True},
                    "hosts": None
                },
                {
                    self.zone_name_key: "zone-2",
                    self.zone_state_key: {"available": False},
                    "hosts": None
                }
            ]
        }
        httpretty.register_uri(httpretty.GET, self.url(),
                               body=jsonutils.dumps(get_os_availability_zone),
                               content_type='application/json')

        get_os_zone_detail = {
            self.zone_info_key: [
                {
                    self.zone_name_key: "zone-1",
                    self.zone_state_key: {"available": True},
                    "hosts": {
                        "fake_host-1": {
                            "nova-compute": {
                                "active": True,
                                "available": True,
                                "updated_at": '2012-12-26 14:45:25'
                            }
                        }
                    }
                },
                {
                    self.zone_name_key: "internal",
                    self.zone_state_key: {"available": True},
                    "hosts": {
                        "fake_host-1": {
                            "nova-sched": {
                                "active": True,
                                "available": True,
                                "updated_at": '2012-12-26 14:45:25'
                            }
                        },
                        "fake_host-2": {
                            "nova-network": {
                                "active": True,
                                "available": False,
                                "updated_at": '2012-12-26 14:45:24'
                            }
                        }
                    }
                },
                {
                    self.zone_name_key: "zone-2",
                    self.zone_state_key: {"available": False},
                    "hosts": None
                }
            ]
        }

        httpretty.register_uri(httpretty.GET, self.url('detail'),
                               body=jsonutils.dumps(get_os_zone_detail),
                               content_type='application/json')


class V3(V1):
    zone_info_key = 'availability_zone_info'
    zone_name_key = 'zone_name'
    zone_state_key = 'zone_state'

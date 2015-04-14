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

from datetime import datetime
from cinderclient.tests.fixture_data import base

# FIXME(jamielennox): use timeutils from oslo
FORMAT = '%Y-%m-%d %H:%M:%S'


class Fixture(base.Fixture):

    base_url = 'os-availability-zone'

    def setUp(self):
        super(Fixture, self).setUp()

        get_availability = {
            "availabilityZoneInfo": [
                {
                    "zoneName": "zone-1",
                    "zoneState": {"available": True},
                    "hosts": None,
                },
                {
                    "zoneName": "zone-2",
                    "zoneState": {"available": False},
                    "hosts": None,
                },
            ]
        }
        self.requests.register_uri('GET', self.url(), json=get_availability)

        updated_1 = datetime(2012, 12, 26, 14, 45, 25, 0).strftime(FORMAT)
        updated_2 = datetime(2012, 12, 26, 14, 45, 24, 0).strftime(FORMAT)
        get_detail = {
            "availabilityZoneInfo": [
                {
                    "zoneName": "zone-1",
                    "zoneState": {"available": True},
                    "hosts": {
                        "fake_host-1": {
                            "cinder-volume": {
                                "active": True,
                                "available": True,
                                "updated_at": updated_1,
                            }
                        }
                    }
                },
                {
                    "zoneName": "internal",
                    "zoneState": {"available": True},
                    "hosts": {
                        "fake_host-1": {
                            "cinder-sched": {
                                "active": True,
                                "available": True,
                                "updated_at": updated_2,
                            }
                        }
                    }
                },
                {
                    "zoneName": "zone-2",
                    "zoneState": {"available": False},
                    "hosts": None,
                },
            ]
        }
        self.requests.register_uri('GET', self.url('detail'), json=get_detail)

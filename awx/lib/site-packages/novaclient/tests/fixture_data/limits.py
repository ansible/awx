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

from novaclient.tests.fixture_data import base


class Fixture(base.Fixture):

    base_url = 'limits'

    def setUp(self):
        super(Fixture, self).setUp()

        get_limits = {
            "limits": {
                "rate": [
                    {
                        "uri": "*",
                        "regex": ".*",
                        "limit": [
                            {
                                "value": 10,
                                "verb": "POST",
                                "remaining": 2,
                                "unit": "MINUTE",
                                "next-available": "2011-12-15T22:42:45Z"
                            },
                            {
                                "value": 10,
                                "verb": "PUT",
                                "remaining": 2,
                                "unit": "MINUTE",
                                "next-available": "2011-12-15T22:42:45Z"
                            },
                            {
                                "value": 100,
                                "verb": "DELETE",
                                "remaining": 100,
                                "unit": "MINUTE",
                                "next-available": "2011-12-15T22:42:45Z"
                            }
                        ]
                    },
                    {
                        "uri": "*/servers",
                        "regex": "^/servers",
                        "limit": [
                            {
                                "verb": "POST",
                                "value": 25,
                                "remaining": 24,
                                "unit": "DAY",
                                "next-available": "2011-12-15T22:42:45Z"
                            }
                        ]
                    }
                ],
                "absolute": {
                    "maxTotalRAMSize": 51200,
                    "maxServerMeta": 5,
                    "maxImageMeta": 5,
                    "maxPersonality": 5,
                    "maxPersonalitySize": 10240
                },
            },
        }

        headers = {'Content-Type': 'application/json'}
        self.requests.register_uri('GET', self.url(),
                                   json=get_limits,
                                   headers=headers)

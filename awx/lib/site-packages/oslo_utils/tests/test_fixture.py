
# Copyright 2015 OpenStack Foundation
# All Rights Reserved.
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

import datetime

from oslotest import base as test_base

from oslo_utils import fixture
from oslo_utils import timeutils


class TimeFixtureTest(test_base.BaseTestCase):

    def test_set_time_override_using_default(self):
        # When the fixture is used with its default constructor, the
        # override_time is set to the current timestamp.
        # Also, when the fixture is cleaned up, the override_time is reset.

        self.assertIsNone(timeutils.utcnow.override_time)
        with fixture.TimeFixture():
            self.assertIsNotNone(timeutils.utcnow.override_time)
        self.assertIsNone(timeutils.utcnow.override_time)

    def test_set_time_override(self):
        # When the fixture is used to set a time, utcnow returns that time.

        new_time = datetime.datetime(2015, 1, 2, 3, 4, 6, 7)
        self.useFixture(fixture.TimeFixture(new_time))
        self.assertEqual(new_time, timeutils.utcnow())
        # Call again to make sure it keeps returning the same time.
        self.assertEqual(new_time, timeutils.utcnow())

    def test_advance_time_delta(self):
        # advance_time_delta() advances the overridden time by some timedelta.

        new_time = datetime.datetime(2015, 1, 2, 3, 4, 6, 7)
        time_fixture = self.useFixture(fixture.TimeFixture(new_time))
        time_fixture.advance_time_delta(datetime.timedelta(seconds=1))
        expected_time = datetime.datetime(2015, 1, 2, 3, 4, 7, 7)
        self.assertEqual(expected_time, timeutils.utcnow())

    def test_advance_time_seconds(self):
        # advance_time_seconds() advances the overridden time by some number of
        # seconds.

        new_time = datetime.datetime(2015, 1, 2, 3, 4, 6, 7)
        time_fixture = self.useFixture(fixture.TimeFixture(new_time))
        time_fixture.advance_time_seconds(2)
        expected_time = datetime.datetime(2015, 1, 2, 3, 4, 8, 7)
        self.assertEqual(expected_time, timeutils.utcnow())

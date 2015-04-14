# Copyright 2012, Red Hat, Inc.
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

import warnings

import mock
from oslotest import base as test_base
import six

from oslo_utils import eventletutils


class EventletUtilsTest(test_base.BaseTestCase):
    def setUp(self):
        super(EventletUtilsTest, self).setUp()
        self._old_avail = eventletutils.EVENTLET_AVAILABLE
        eventletutils.EVENTLET_AVAILABLE = True

    def tearDown(self):
        super(EventletUtilsTest, self).tearDown()
        eventletutils.EVENTLET_AVAILABLE = self._old_avail

    @mock.patch("oslo_utils.eventletutils._patcher")
    def test_warning_not_patched(self, mock_patcher):
        mock_patcher.already_patched = True
        mock_patcher.is_monkey_patched.return_value = False
        with warnings.catch_warnings(record=True) as capture:
            warnings.simplefilter("always")
            eventletutils.warn_eventlet_not_patched(['os'])
        self.assertEqual(1, len(capture))
        w = capture[0]
        self.assertEqual(RuntimeWarning, w.category)
        self.assertIn('os', six.text_type(w.message))

    @mock.patch("oslo_utils.eventletutils._patcher")
    def test_warning_not_patched_none_provided(self, mock_patcher):
        mock_patcher.already_patched = True
        mock_patcher.is_monkey_patched.return_value = False
        with warnings.catch_warnings(record=True) as capture:
            warnings.simplefilter("always")
            eventletutils.warn_eventlet_not_patched()
        self.assertEqual(1, len(capture))
        w = capture[0]
        self.assertEqual(RuntimeWarning, w.category)
        for m in eventletutils._ALL_PATCH:
            self.assertIn(m, six.text_type(w.message))

    @mock.patch("oslo_utils.eventletutils._patcher")
    def test_warning_not_patched_all(self, mock_patcher):
        mock_patcher.already_patched = True
        mock_patcher.is_monkey_patched.return_value = False
        with warnings.catch_warnings(record=True) as capture:
            warnings.simplefilter("always")
            eventletutils.warn_eventlet_not_patched(['all'])
        self.assertEqual(1, len(capture))
        w = capture[0]
        self.assertEqual(RuntimeWarning, w.category)
        for m in eventletutils._ALL_PATCH:
            self.assertIn(m, six.text_type(w.message))

    @mock.patch("oslo_utils.eventletutils._patcher")
    def test_no_warning(self, mock_patcher):
        mock_patcher.already_patched = True
        mock_patcher.is_monkey_patched.return_value = True
        with warnings.catch_warnings(record=True) as capture:
            warnings.simplefilter("always")
            eventletutils.warn_eventlet_not_patched(['os'])
        self.assertEqual(0, len(capture))

    @mock.patch("oslo_utils.eventletutils._patcher")
    def test_partially_patched_warning(self, mock_patcher):
        is_patched = set()
        mock_patcher.already_patched = True
        mock_patcher.is_monkey_patched.side_effect = lambda m: m in is_patched
        with warnings.catch_warnings(record=True) as capture:
            warnings.simplefilter("always")
            eventletutils.warn_eventlet_not_patched(['os'])
        self.assertEqual(1, len(capture))
        is_patched.add('os')
        with warnings.catch_warnings(record=True) as capture:
            warnings.simplefilter("always")
            eventletutils.warn_eventlet_not_patched(['os'])
        self.assertEqual(0, len(capture))
        is_patched.add('thread')
        with warnings.catch_warnings(record=True) as capture:
            warnings.simplefilter("always")
            eventletutils.warn_eventlet_not_patched(['os', 'thread'])
        self.assertEqual(0, len(capture))
        with warnings.catch_warnings(record=True) as capture:
            warnings.simplefilter("always")
            eventletutils.warn_eventlet_not_patched(['all'])
        self.assertEqual(1, len(capture))
        w = capture[0]
        self.assertEqual(RuntimeWarning, w.category)
        for m in ['os', 'thread']:
            self.assertNotIn(m, six.text_type(w.message))

    def test_invalid_patch_check(self):
        self.assertRaises(ValueError,
                          eventletutils.warn_eventlet_not_patched,
                          ['blah.blah'])

# Copyright 2012 Red Hat, Inc.
# Copyright 2013 IBM Corp.
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

from oslotest import base as test_base

from oslo_i18n import _lazy


class LazyTest(test_base.BaseTestCase):

    def setUp(self):
        super(LazyTest, self).setUp()
        self._USE_LAZY = _lazy.USE_LAZY

    def tearDown(self):
        _lazy.USE_LAZY = self._USE_LAZY
        super(LazyTest, self).tearDown()

    def test_enable_lazy(self):
        _lazy.USE_LAZY = False
        _lazy.enable_lazy()
        self.assertTrue(_lazy.USE_LAZY)

    def test_disable_lazy(self):
        _lazy.USE_LAZY = True
        _lazy.enable_lazy(False)
        self.assertFalse(_lazy.USE_LAZY)

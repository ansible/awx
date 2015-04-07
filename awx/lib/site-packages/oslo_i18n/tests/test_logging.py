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

import mock
from oslotest import base as test_base

from oslo_i18n import _factory


class LogLevelTranslationsTest(test_base.BaseTestCase):

    def test_info(self):
        self._test('info')

    def test_warning(self):
        self._test('warning')

    def test_error(self):
        self._test('error')

    def test_critical(self):
        self._test('critical')

    def _test(self, level):
        with mock.patch.object(_factory.TranslatorFactory,
                               '_make_translation_func') as mtf:
            tf = _factory.TranslatorFactory('domain')
            getattr(tf, 'log_%s' % level)
            mtf.assert_called_with('domain-log-%s' % level)

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
import six

from oslo_i18n import _factory
from oslo_i18n import _lazy
from oslo_i18n import _message


class TranslatorFactoryTest(test_base.BaseTestCase):

    def setUp(self):
        super(TranslatorFactoryTest, self).setUp()
        # remember so we can reset to it later in case it changes
        self._USE_LAZY = _lazy.USE_LAZY

    def tearDown(self):
        # reset to value before test
        _lazy.USE_LAZY = self._USE_LAZY
        super(TranslatorFactoryTest, self).tearDown()

    def test_lazy(self):
        _lazy.enable_lazy(True)
        with mock.patch.object(_message, 'Message') as msg:
            tf = _factory.TranslatorFactory('domain')
            tf.primary('some text')
            msg.assert_called_with('some text', domain='domain')

    def test_not_lazy(self):
        _lazy.enable_lazy(False)
        with mock.patch.object(_message, 'Message') as msg:
            msg.side_effect = AssertionError('should not use Message')
            tf = _factory.TranslatorFactory('domain')
            tf.primary('some text')

    def test_change_lazy(self):
        _lazy.enable_lazy(True)
        tf = _factory.TranslatorFactory('domain')
        r = tf.primary('some text')
        self.assertIsInstance(r, _message.Message)
        _lazy.enable_lazy(False)
        r = tf.primary('some text')
        # Python 2.6 doesn't have assertNotIsInstance().
        self.assertFalse(isinstance(r, _message.Message))

    def test_py2(self):
        _lazy.enable_lazy(False)
        with mock.patch.object(six, 'PY3', False):
            with mock.patch('gettext.translation') as translation:
                trans = mock.Mock()
                translation.return_value = trans
                trans.gettext.side_effect = AssertionError(
                    'should have called ugettext')
                tf = _factory.TranslatorFactory('domain')
                tf.primary('some text')
                trans.ugettext.assert_called_with('some text')

    def test_py3(self):
        _lazy.enable_lazy(False)
        with mock.patch.object(six, 'PY3', True):
            with mock.patch('gettext.translation') as translation:
                trans = mock.Mock()
                translation.return_value = trans
                trans.ugettext.side_effect = AssertionError(
                    'should have called gettext')
                tf = _factory.TranslatorFactory('domain')
                tf.primary('some text')
                trans.gettext.assert_called_with('some text')

    def test_log_level_domain_name(self):
        with mock.patch.object(_factory.TranslatorFactory,
                               '_make_translation_func') as mtf:
            tf = _factory.TranslatorFactory('domain')
            tf._make_log_translation_func('mylevel')
            mtf.assert_called_with('domain-log-mylevel')

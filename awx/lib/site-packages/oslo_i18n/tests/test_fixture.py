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
import six

from oslo import i18n as old_i18n
import oslo_i18n as new_i18n
from oslo_i18n import _gettextutils
from oslo_i18n._i18n import _
from oslo_i18n import _lazy
from oslo_i18n import _message
from oslo_i18n import _translate
from oslo_i18n import fixture


class TranslationFixtureTest(test_base.BaseTestCase):

    def setUp(self):
        super(TranslationFixtureTest, self).setUp()
        self.trans_fixture = self.useFixture(fixture.Translation())

    def test_lazy(self):
        msg = self.trans_fixture.lazy('this is a lazy message')
        self.assertIsInstance(msg, _message.Message)
        self.assertEqual(msg.msgid, 'this is a lazy message')

    def test_immediate(self):
        msg = self.trans_fixture.immediate('this is a lazy message')
        # Python 2.6 does not have assertNotIsInstance
        self.assertFalse(isinstance(msg, _message.Message))
        self.assertIsInstance(msg, six.text_type)
        self.assertEqual(msg, u'this is a lazy message')


class ToggleLazyFixtureText(test_base.BaseTestCase):

    def test_on_on(self):
        _lazy.USE_LAZY = True
        f = fixture.ToggleLazy(True)
        f.setUp()
        self.assertTrue(_lazy.USE_LAZY)
        f._restore_original()
        self.assertTrue(_lazy.USE_LAZY)

    def test_on_off(self):
        _lazy.USE_LAZY = True
        f = fixture.ToggleLazy(False)
        f.setUp()
        self.assertFalse(_lazy.USE_LAZY)
        f._restore_original()
        self.assertTrue(_lazy.USE_LAZY)

    def test_off_on(self):
        _lazy.USE_LAZY = False
        f = fixture.ToggleLazy(True)
        f.setUp()
        self.assertTrue(_lazy.USE_LAZY)
        f._restore_original()
        self.assertFalse(_lazy.USE_LAZY)

    def test_off_off(self):
        _lazy.USE_LAZY = False
        f = fixture.ToggleLazy(False)
        f.setUp()
        self.assertFalse(_lazy.USE_LAZY)
        f._restore_original()
        self.assertFalse(_lazy.USE_LAZY)


_FAKE_LANG = 'en_ZZ'


class PrefixLazyTranslationTest(test_base.BaseTestCase):

    def test_default(self):

        # Turn lazy off to check that fixture turns it on
        self.useFixture(fixture.ToggleLazy(False))
        self.useFixture(fixture.PrefixLazyTranslation())
        self.assertTrue(_lazy.USE_LAZY)
        default_lang = fixture.PrefixLazyTranslation._DEFAULT_LANG
        raw_id1 = 'fake msg1'
        expected_msg = 'oslo.i18n/' + default_lang + ': ' + raw_id1
        msg1 = _(raw_id1)    # noqa
        self.assertEqual([default_lang],
                         _gettextutils.get_available_languages('oslo'))
        self.assertEqual([default_lang],
                         old_i18n.get_available_languages('oslo'))
        self.assertEqual([default_lang],
                         new_i18n.get_available_languages('oslo'))
        self.assertEqual(expected_msg, _translate.translate(msg1))

    def test_extra_lang(self):
        languages = _gettextutils.get_available_languages('oslo')
        languages.append(_FAKE_LANG)
        self.useFixture(fixture.PrefixLazyTranslation(languages=languages))
        raw_id1 = 'fake msg1'
        expected_msg_en_US = ('oslo.i18n/' +
                              fixture.PrefixLazyTranslation._DEFAULT_LANG +
                              ': ' + raw_id1)
        expected_msg_en_ZZ = 'oslo.i18n/' + _FAKE_LANG + ': ' + raw_id1
        msg1 = _(raw_id1)     # noqa
        self.assertEqual(languages,
                         _gettextutils.get_available_languages('oslo'))
        self.assertEqual(languages,
                         old_i18n.get_available_languages('oslo'))
        self.assertEqual(languages,
                         new_i18n.get_available_languages('oslo'))
        self.assertEqual(expected_msg_en_US, _translate.translate(msg1))
        self.assertEqual(expected_msg_en_ZZ,
                         _translate.translate(msg1,
                                              desired_locale=_FAKE_LANG))

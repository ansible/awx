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

import gettext
import logging

from babel import localedata
import mock
from oslotest import base as test_base
from oslotest import moxstubout
import six

from oslo_i18n import _factory
from oslo_i18n import _gettextutils
from oslo_i18n import _lazy
from oslo_i18n import _message


LOG = logging.getLogger(__name__)


class GettextTest(test_base.BaseTestCase):

    def setUp(self):
        super(GettextTest, self).setUp()
        moxfixture = self.useFixture(moxstubout.MoxStubout())
        self.stubs = moxfixture.stubs
        self.mox = moxfixture.mox
        # remember so we can reset to it later in case it changes
        self._USE_LAZY = _lazy.USE_LAZY
        self.t = _factory.TranslatorFactory('oslo_i18n.test')

    def tearDown(self):
        # reset to value before test
        _lazy.USE_LAZY = self._USE_LAZY
        super(GettextTest, self).tearDown()

    def test_gettext_does_not_blow_up(self):
        LOG.info(self.t.primary('test'))

    def test__gettextutils_install(self):
        _gettextutils.install('blaa')
        _lazy.enable_lazy(False)
        self.assertTrue(isinstance(self.t.primary('A String'),
                                   six.text_type))

        _gettextutils.install('blaa')
        _lazy.enable_lazy(True)
        self.assertTrue(isinstance(self.t.primary('A Message'),
                                   _message.Message))

    def test_gettext_install_looks_up_localedir(self):
        with mock.patch('os.environ.get') as environ_get:
            with mock.patch('gettext.install'):
                environ_get.return_value = '/foo/bar'
                _gettextutils.install('blaa')
                environ_get.assert_calls([mock.call('BLAA_LOCALEDIR')])

    def test_gettext_install_updates_builtins(self):
        with mock.patch('os.environ.get') as environ_get:
            with mock.patch('gettext.install'):
                environ_get.return_value = '/foo/bar'
                if '_' in six.moves.builtins.__dict__:
                    del six.moves.builtins.__dict__['_']
                _gettextutils.install('blaa')
                self.assertIn('_', six.moves.builtins.__dict__)

    def test_get_available_languages(self):
        # All the available languages for which locale data is available
        def _mock_locale_identifiers():
            # 'zh', 'zh_Hant'. 'zh_Hant_HK', 'fil' all have aliases
            # missing from babel but we add them in _gettextutils, we
            # test that here too
            return ['zh', 'es', 'nl', 'fr', 'zh_Hant', 'zh_Hant_HK', 'fil']

        self.stubs.Set(localedata,
                       'list' if hasattr(localedata, 'list')
                       else 'locale_identifiers',
                       _mock_locale_identifiers)

        # Only the languages available for a specific translation domain
        def _mock_gettext_find(domain, localedir=None, languages=None, all=0):
            languages = languages or []
            if domain == 'domain_1':
                return 'translation-file' if any(x in ['zh', 'es', 'fil']
                                                 for x in languages) else None
            elif domain == 'domain_2':
                return 'translation-file' if any(x in ['fr', 'zh_Hant']
                                                 for x in languages) else None
            return None
        self.stubs.Set(gettext, 'find', _mock_gettext_find)

        # Ensure that no domains are cached
        _gettextutils._AVAILABLE_LANGUAGES = {}

        # en_US should always be available no matter the domain
        # and it should also always be the first element since order matters
        domain_1_languages = _gettextutils.get_available_languages('domain_1')
        domain_2_languages = _gettextutils.get_available_languages('domain_2')
        self.assertEqual('en_US', domain_1_languages[0])
        self.assertEqual('en_US', domain_2_languages[0])
        # The domain languages should be included after en_US with
        # with their respective aliases when it applies
        self.assertEqual(6, len(domain_1_languages))
        self.assertIn('zh', domain_1_languages)
        self.assertIn('zh_CN', domain_1_languages)
        self.assertIn('es', domain_1_languages)
        self.assertIn('fil', domain_1_languages)
        self.assertIn('tl_PH', domain_1_languages)
        self.assertEqual(4, len(domain_2_languages))
        self.assertIn('fr', domain_2_languages)
        self.assertIn('zh_Hant', domain_2_languages)
        self.assertIn('zh_TW', domain_2_languages)
        self.assertEqual(2, len(_gettextutils._AVAILABLE_LANGUAGES))
        # Now test an unknown domain, only en_US should be included
        unknown_domain_languages = _gettextutils.get_available_languages('huh')
        self.assertEqual(1, len(unknown_domain_languages))
        self.assertIn('en_US', unknown_domain_languages)

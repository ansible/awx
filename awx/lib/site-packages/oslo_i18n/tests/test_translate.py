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

from __future__ import unicode_literals

import mock
from oslotest import base as test_base

from oslo_i18n import _message
from oslo_i18n import _translate
from oslo_i18n.tests import fakes
from oslo_i18n.tests import utils


class TranslateTest(test_base.BaseTestCase):

    @mock.patch('gettext.translation')
    def test_translate(self, mock_translation):
        en_message = 'A message in the default locale'
        es_translation = 'A message in Spanish'
        message = _message.Message(en_message)

        es_translations = {en_message: es_translation}
        translations_map = {'es': es_translations}
        translator = fakes.FakeTranslations.translator(translations_map)
        mock_translation.side_effect = translator

        # translate() works on msgs and on objects whose unicode reps are msgs
        obj = utils.SomeObject(message)
        self.assertEqual(es_translation, _translate.translate(message, 'es'))
        self.assertEqual(es_translation, _translate.translate(obj, 'es'))

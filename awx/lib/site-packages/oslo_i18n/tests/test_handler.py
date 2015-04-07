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

import logging

import mock
from oslotest import base as test_base
import six

from oslo_i18n import _message
from oslo_i18n import log as i18n_log
from oslo_i18n.tests import fakes

LOG = logging.getLogger(__name__)


class TranslationHandlerTestCase(test_base.BaseTestCase):

    def setUp(self):
        super(TranslationHandlerTestCase, self).setUp()

        self.stream = six.StringIO()
        self.destination_handler = logging.StreamHandler(self.stream)
        self.translation_handler = i18n_log.TranslationHandler('zh_CN')
        self.translation_handler.setTarget(self.destination_handler)

        self.logger = logging.getLogger('localehander_logger')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(self.translation_handler)

    def test_set_formatter(self):
        formatter = 'some formatter'
        self.translation_handler.setFormatter(formatter)
        self.assertEqual(formatter, self.translation_handler.target.formatter)

    @mock.patch('gettext.translation')
    def test_emit_translated_message(self, mock_translation):
        log_message = 'A message to be logged'
        log_message_translation = 'A message to be logged in Chinese'
        translations = {log_message: log_message_translation}
        translations_map = {'zh_CN': translations}
        translator = fakes.FakeTranslations.translator(translations_map)
        mock_translation.side_effect = translator

        msg = _message.Message(log_message)

        self.logger.info(msg)
        self.assertIn(log_message_translation, self.stream.getvalue())

    @mock.patch('gettext.translation')
    def test_emit_translated_message_with_args(self, mock_translation):
        log_message = 'A message to be logged %s'
        log_message_translation = 'A message to be logged in Chinese %s'
        log_arg = 'Arg to be logged'
        log_arg_translation = 'An arg to be logged in Chinese'

        translations = {log_message: log_message_translation,
                        log_arg: log_arg_translation}
        translations_map = {'zh_CN': translations}
        translator = fakes.FakeTranslations.translator(translations_map)
        mock_translation.side_effect = translator

        msg = _message.Message(log_message)
        arg = _message.Message(log_arg)

        self.logger.info(msg, arg)
        self.assertIn(log_message_translation % log_arg_translation,
                      self.stream.getvalue())

    @mock.patch('gettext.translation')
    def test_emit_translated_message_with_named_args(self, mock_translation):
        log_message = 'A message to be logged %(arg1)s $(arg2)s'
        log_message_translation = 'Chinese msg to be logged %(arg1)s $(arg2)s'
        log_arg_1 = 'Arg1 to be logged'
        log_arg_1_translation = 'Arg1 to be logged in Chinese'
        log_arg_2 = 'Arg2 to be logged'
        log_arg_2_translation = 'Arg2 to be logged in Chinese'

        translations = {log_message: log_message_translation,
                        log_arg_1: log_arg_1_translation,
                        log_arg_2: log_arg_2_translation}
        translations_map = {'zh_CN': translations}
        translator = fakes.FakeTranslations.translator(translations_map)
        mock_translation.side_effect = translator

        msg = _message.Message(log_message)
        arg_1 = _message.Message(log_arg_1)
        arg_2 = _message.Message(log_arg_2)

        self.logger.info(msg, {'arg1': arg_1, 'arg2': arg_2})
        translation = log_message_translation % {'arg1': log_arg_1_translation,
                                                 'arg2': log_arg_2_translation}
        self.assertIn(translation, self.stream.getvalue())

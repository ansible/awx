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

import logging

import mock
from oslotest import base as test_base
import six
import testtools

from oslo_i18n import _message
from oslo_i18n.tests import fakes
from oslo_i18n.tests import utils

LOG = logging.getLogger(__name__)


class MessageTestCase(test_base.BaseTestCase):
    """Unit tests for locale Message class."""

    def test_message_id_and_message_text(self):
        message = _message.Message('1')
        self.assertEqual('1', message.msgid)
        self.assertEqual('1', message)
        message = _message.Message('1', msgtext='A')
        self.assertEqual('1', message.msgid)
        self.assertEqual('A', message)

    def test_message_is_unicode(self):
        message = _message.Message('some %s') % 'message'
        self.assertIsInstance(message, six.text_type)

    @mock.patch('locale.getdefaultlocale')
    @mock.patch('gettext.translation')
    def test_create_message_non_english_default_locale(self,
                                                       mock_translation,
                                                       mock_getdefaultlocale):
        msgid = 'A message in English'
        es_translation = 'A message in Spanish'

        es_translations = {msgid: es_translation}
        translations_map = {'es': es_translations}
        translator = fakes.FakeTranslations.translator(translations_map)
        mock_translation.side_effect = translator
        mock_getdefaultlocale.return_value = ('es',)

        message = _message.Message(msgid)

        # The base representation of the message is in Spanish, as well as
        # the default translation, since the default locale was Spanish.
        self.assertEqual(es_translation, message)
        self.assertEqual(es_translation, message.translate())

    def test_translate_returns_unicode(self):
        message = _message.Message('some %s') % 'message'
        self.assertIsInstance(message.translate(), six.text_type)

    def test_mod_with_named_parameters(self):
        msgid = ("%(description)s\nCommand: %(cmd)s\n"
                 "Exit code: %(exit_code)s\nStdout: %(stdout)r\n"
                 "Stderr: %(stderr)r %%(something)s")
        params = {'description': 'test1',
                  'cmd': 'test2',
                  'exit_code': 'test3',
                  'stdout': 'test4',
                  'stderr': 'test5',
                  'something': 'trimmed'}

        result = _message.Message(msgid) % params

        expected = msgid % params
        self.assertEqual(result, expected)
        self.assertEqual(result.translate(), expected)

    def test_multiple_mod_with_named_parameter(self):
        msgid = ("%(description)s\nCommand: %(cmd)s\n"
                 "Exit code: %(exit_code)s\nStdout: %(stdout)r\n"
                 "Stderr: %(stderr)r")
        params = {'description': 'test1',
                  'cmd': 'test2',
                  'exit_code': 'test3',
                  'stdout': 'test4',
                  'stderr': 'test5'}

        # Run string interpolation the first time to make a new Message
        first = _message.Message(msgid) % params

        # Run string interpolation on the new Message, to replicate
        # one of the error paths with some Exception classes we've
        # implemented in OpenStack. We should receive a second Message
        # object, but the translation results should be the same.
        #
        # The production code that triggers this problem does something
        # like:
        #
        #    msg = _('there was a problem %(name)s') % {'name': 'some value'}
        #    LOG.error(msg)
        #    raise BadExceptionClass(msg)
        #
        # where BadExceptionClass does something like:
        #
        #    class BadExceptionClass(Exception):
        #      def __init__(self, msg, **kwds):
        #         super(BadExceptionClass, self).__init__(msg % kwds)
        #
        expected = first % {}

        # Base message id should be the same
        self.assertEqual(first.msgid, expected.msgid)

        # Preserved arguments should be the same
        self.assertEqual(first.params, expected.params)

        # Should have different objects
        self.assertIsNot(expected, first)

        # Final translations should be the same
        self.assertEqual(expected.translate(), first.translate())

    def test_mod_with_named_parameters_no_space(self):
        msgid = ("Request: %(method)s http://%(server)s:"
                 "%(port)s%(url)s with headers %(headers)s")
        params = {'method': 'POST',
                  'server': 'test1',
                  'port': 1234,
                  'url': 'test2',
                  'headers': {'h1': 'val1'}}

        result = _message.Message(msgid) % params

        expected = msgid % params
        self.assertEqual(result, expected)
        self.assertEqual(result.translate(), expected)

    def test_mod_with_dict_parameter(self):
        msgid = "Test that we can inject a dictionary %s"
        params = {'description': 'test1'}

        result = _message.Message(msgid) % params

        expected = msgid % params
        self.assertEqual(expected, result)
        self.assertEqual(expected, result.translate())

    def test_mod_with_integer_parameters(self):
        msgid = "Some string with params: %d"
        params = [0, 1, 10, 24124]

        messages = []
        results = []
        for param in params:
            messages.append(msgid % param)
            results.append(_message.Message(msgid) % param)

        for message, result in zip(messages, results):
            self.assertEqual(type(result), _message.Message)
            self.assertEqual(result.translate(), message)

            # simulate writing out as string
            result_str = '%s' % result.translate()
            self.assertEqual(result_str, message)
            self.assertEqual(result, message)

    def test_mod_copies_parameters(self):
        msgid = "Found object: %(current_value)s"
        changing_dict = {'current_value': 1}
        # A message created with some params
        result = _message.Message(msgid) % changing_dict
        # The parameters may change
        changing_dict['current_value'] = 2
        # Even if the param changes when the message is
        # translated it should use the original param
        self.assertEqual(result.translate(), 'Found object: 1')

    def test_mod_deep_copies_parameters(self):
        msgid = "Found list: %(current_list)s"
        changing_list = list([1, 2, 3])
        params = {'current_list': changing_list}
        # Apply the params
        result = _message.Message(msgid) % params
        # Change the list
        changing_list.append(4)
        # Even though the list changed the message
        # translation should use the original list
        self.assertEqual(result.translate(), "Found list: [1, 2, 3]")

    def test_mod_deep_copies_param_nodeep_param(self):
        msgid = "Value: %s"
        params = utils.NoDeepCopyObject(5)
        # Apply the params
        result = _message.Message(msgid) % params
        self.assertEqual(result.translate(), "Value: 5")

    def test_mod_deep_copies_param_nodeep_dict(self):
        msgid = "Values: %(val1)s %(val2)s"
        params = {'val1': 1, 'val2': utils.NoDeepCopyObject(2)}
        # Apply the params
        result = _message.Message(msgid) % params
        self.assertEqual(result.translate(), "Values: 1 2")

        # Apply again to make sure other path works as well
        params = {'val1': 3, 'val2': utils.NoDeepCopyObject(4)}
        result = _message.Message(msgid) % params
        self.assertEqual(result.translate(), "Values: 3 4")

    def test_mod_returns_a_copy(self):
        msgid = "Some msgid string: %(test1)s %(test2)s"
        message = _message.Message(msgid)
        m1 = message % {'test1': 'foo', 'test2': 'bar'}
        m2 = message % {'test1': 'foo2', 'test2': 'bar2'}

        self.assertIsNot(message, m1)
        self.assertIsNot(message, m2)
        self.assertEqual(m1.translate(),
                         msgid % {'test1': 'foo', 'test2': 'bar'})
        self.assertEqual(m2.translate(),
                         msgid % {'test1': 'foo2', 'test2': 'bar2'})

    def test_mod_with_none_parameter(self):
        msgid = "Some string with params: %s"
        message = _message.Message(msgid) % None
        self.assertEqual(msgid % None, message)
        self.assertEqual(msgid % None, message.translate())

    def test_mod_with_missing_parameters(self):
        msgid = "Some string with params: %s %s"
        test_me = lambda: _message.Message(msgid) % 'just one'
        # Just like with strings missing parameters raise TypeError
        self.assertRaises(TypeError, test_me)

    def test_mod_with_extra_parameters(self):
        msgid = "Some string with params: %(param1)s %(param2)s"
        params = {'param1': 'test',
                  'param2': 'test2',
                  'param3': 'notinstring'}

        result = _message.Message(msgid) % params

        expected = msgid % params
        self.assertEqual(result, expected)
        self.assertEqual(result.translate(), expected)

        # Make sure unused params still there
        self.assertEqual(result.params.keys(), params.keys())

    def test_mod_with_missing_named_parameters(self):
        msgid = ("Some string with params: %(param1)s %(param2)s"
                 " and a missing one %(missing)s")
        params = {'param1': 'test',
                  'param2': 'test2'}

        test_me = lambda: _message.Message(msgid) % params
        # Just like with strings missing named parameters raise KeyError
        self.assertRaises(KeyError, test_me)

    def test_add_disabled(self):
        msgid = "A message"
        test_me = lambda: _message.Message(msgid) + ' some string'
        self.assertRaises(TypeError, test_me)

    def test_radd_disabled(self):
        msgid = "A message"
        test_me = lambda: utils.SomeObject('test') + _message.Message(msgid)
        self.assertRaises(TypeError, test_me)

    @testtools.skipIf(six.PY3, 'test specific to Python 2')
    def test_str_disabled(self):
        msgid = "A message"
        test_me = lambda: str(_message.Message(msgid))
        self.assertRaises(UnicodeError, test_me)

    @mock.patch('gettext.translation')
    def test_translate(self, mock_translation):
        en_message = 'A message in the default locale'
        es_translation = 'A message in Spanish'
        message = _message.Message(en_message)

        es_translations = {en_message: es_translation}
        translations_map = {'es': es_translations}
        translator = fakes.FakeTranslations.translator(translations_map)
        mock_translation.side_effect = translator

        self.assertEqual(es_translation, message.translate('es'))

    @mock.patch('gettext.translation')
    def test_translate_message_from_unicoded_object(self, mock_translation):
        en_message = 'A message in the default locale'
        es_translation = 'A message in Spanish'
        message = _message.Message(en_message)
        es_translations = {en_message: es_translation}
        translations_map = {'es': es_translations}
        translator = fakes.FakeTranslations.translator(translations_map)
        mock_translation.side_effect = translator

        # Here we are not testing the Message object directly but the result
        # of unicoding() an object whose unicode representation is a Message
        obj = utils.SomeObject(message)
        unicoded_obj = six.text_type(obj)

        self.assertEqual(es_translation, unicoded_obj.translate('es'))

    @mock.patch('gettext.translation')
    def test_translate_multiple_languages(self, mock_translation):
        en_message = 'A message in the default locale'
        es_translation = 'A message in Spanish'
        zh_translation = 'A message in Chinese'
        message = _message.Message(en_message)

        es_translations = {en_message: es_translation}
        zh_translations = {en_message: zh_translation}
        translations_map = {'es': es_translations,
                            'zh': zh_translations}
        translator = fakes.FakeTranslations.translator(translations_map)
        mock_translation.side_effect = translator

        self.assertEqual(es_translation, message.translate('es'))
        self.assertEqual(zh_translation, message.translate('zh'))
        self.assertEqual(en_message, message.translate(None))
        self.assertEqual(en_message, message.translate('en'))
        self.assertEqual(en_message, message.translate('XX'))

    @mock.patch('gettext.translation')
    def test_translate_message_with_param(self, mock_translation):
        message_with_params = 'A message: %s'
        es_translation = 'A message in Spanish: %s'
        param = 'A Message param'

        translations = {message_with_params: es_translation}
        translator = fakes.FakeTranslations.translator({'es': translations})
        mock_translation.side_effect = translator

        msg = _message.Message(message_with_params)
        msg = msg % param

        default_translation = message_with_params % param
        expected_translation = es_translation % param
        self.assertEqual(expected_translation, msg.translate('es'))
        self.assertEqual(default_translation, msg.translate('XX'))

    @mock.patch('gettext.translation')
    def test_translate_message_with_object_param(self, mock_translation):
        message_with_params = 'A message: %s'
        es_translation = 'A message in Spanish: %s'
        param = 'A Message param'
        param_translation = 'A Message param in Spanish'

        translations = {message_with_params: es_translation,
                        param: param_translation}
        translator = fakes.FakeTranslations.translator({'es': translations})
        mock_translation.side_effect = translator

        msg = _message.Message(message_with_params)
        param_msg = _message.Message(param)

        # Here we are testing translation of a Message with another object
        # that can be translated via its unicode() representation, this is
        # very common for instance when modding an Exception with a Message
        obj = utils.SomeObject(param_msg)
        msg = msg % obj

        default_translation = message_with_params % param
        expected_translation = es_translation % param_translation

        self.assertEqual(expected_translation, msg.translate('es'))
        self.assertEqual(default_translation, msg.translate('XX'))

    @mock.patch('gettext.translation')
    def test_translate_message_with_param_from_unicoded_obj(self,
                                                            mock_translation):
        message_with_params = 'A message: %s'
        es_translation = 'A message in Spanish: %s'
        param = 'A Message param'

        translations = {message_with_params: es_translation}
        translator = fakes.FakeTranslations.translator({'es': translations})
        mock_translation.side_effect = translator

        msg = _message.Message(message_with_params)
        msg = msg % param

        default_translation = message_with_params % param
        expected_translation = es_translation % param

        obj = utils.SomeObject(msg)
        unicoded_obj = six.text_type(obj)

        self.assertEqual(expected_translation, unicoded_obj.translate('es'))
        self.assertEqual(default_translation, unicoded_obj.translate('XX'))

    @mock.patch('gettext.translation')
    def test_translate_message_with_message_parameter(self, mock_translation):
        message_with_params = 'A message with param: %s'
        es_translation = 'A message with param in Spanish: %s'
        message_param = 'A message param'
        es_param_translation = 'A message param in Spanish'

        translations = {message_with_params: es_translation,
                        message_param: es_param_translation}
        translator = fakes.FakeTranslations.translator({'es': translations})
        mock_translation.side_effect = translator

        msg = _message.Message(message_with_params)
        msg_param = _message.Message(message_param)
        msg = msg % msg_param

        default_translation = message_with_params % message_param
        expected_translation = es_translation % es_param_translation
        self.assertEqual(expected_translation, msg.translate('es'))
        self.assertEqual(default_translation, msg.translate('XX'))

    @mock.patch('gettext.translation')
    def test_translate_message_with_message_parameters(self, mock_translation):
        message_with_params = 'A message with params: %s %s'
        es_translation = 'A message with params in Spanish: %s %s'
        message_param = 'A message param'
        es_param_translation = 'A message param in Spanish'
        another_message_param = 'Another message param'
        another_es_param_translation = 'Another message param in Spanish'

        translations = {message_with_params: es_translation,
                        message_param: es_param_translation,
                        another_message_param: another_es_param_translation}
        translator = fakes.FakeTranslations.translator({'es': translations})
        mock_translation.side_effect = translator

        msg = _message.Message(message_with_params)
        param_1 = _message.Message(message_param)
        param_2 = _message.Message(another_message_param)
        msg = msg % (param_1, param_2)

        default_translation = message_with_params % (message_param,
                                                     another_message_param)
        expected_translation = es_translation % (es_param_translation,
                                                 another_es_param_translation)
        self.assertEqual(expected_translation, msg.translate('es'))
        self.assertEqual(default_translation, msg.translate('XX'))

    @mock.patch('gettext.translation')
    def test_translate_message_with_named_parameters(self, mock_translation):
        message_with_params = 'A message with params: %(param)s'
        es_translation = 'A message with params in Spanish: %(param)s'
        message_param = 'A Message param'
        es_param_translation = 'A message param in Spanish'

        translations = {message_with_params: es_translation,
                        message_param: es_param_translation}
        translator = fakes.FakeTranslations.translator({'es': translations})
        mock_translation.side_effect = translator

        msg = _message.Message(message_with_params)
        msg_param = _message.Message(message_param)
        msg = msg % {'param': msg_param}

        default_translation = message_with_params % {'param': message_param}
        expected_translation = es_translation % {'param': es_param_translation}
        self.assertEqual(expected_translation, msg.translate('es'))
        self.assertEqual(default_translation, msg.translate('XX'))

    @mock.patch('locale.getdefaultlocale')
    @mock.patch('gettext.translation')
    def test_translate_message_non_default_locale(self,
                                                  mock_translation,
                                                  mock_getdefaultlocale):
        message_with_params = 'A message with params: %(param)s'
        es_translation = 'A message with params in Spanish: %(param)s'
        zh_translation = 'A message with params in Chinese: %(param)s'
        fr_translation = 'A message with params in French: %(param)s'

        message_param = 'A Message param'
        es_param_translation = 'A message param in Spanish'
        zh_param_translation = 'A message param in Chinese'
        fr_param_translation = 'A message param in French'

        es_translations = {message_with_params: es_translation,
                           message_param: es_param_translation}
        zh_translations = {message_with_params: zh_translation,
                           message_param: zh_param_translation}
        fr_translations = {message_with_params: fr_translation,
                           message_param: fr_param_translation}

        translator = fakes.FakeTranslations.translator({'es': es_translations,
                                                        'zh': zh_translations,
                                                        'fr': fr_translations})
        mock_translation.side_effect = translator
        mock_getdefaultlocale.return_value = ('es',)

        msg = _message.Message(message_with_params)
        msg_param = _message.Message(message_param)
        msg = msg % {'param': msg_param}

        es_translation = es_translation % {'param': es_param_translation}
        zh_translation = zh_translation % {'param': zh_param_translation}
        fr_translation = fr_translation % {'param': fr_param_translation}

        # Because sys.getdefaultlocale() was Spanish,
        # the default translation will be to Spanish
        self.assertEqual(es_translation, msg)
        self.assertEqual(es_translation, msg.translate())
        self.assertEqual(es_translation, msg.translate('es'))

        # Translation into other locales still works
        self.assertEqual(zh_translation, msg.translate('zh'))
        self.assertEqual(fr_translation, msg.translate('fr'))

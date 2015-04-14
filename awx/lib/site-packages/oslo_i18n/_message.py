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
"""Private Message class for lazy translation support.
"""

import copy
import gettext
import locale
import os

import six

from oslo_i18n import _locale
from oslo_i18n import _translate


class Message(six.text_type):
    """A Message object is a unicode object that can be translated.

    Translation of Message is done explicitly using the translate() method.
    For all non-translation intents and purposes, a Message is simply unicode,
    and can be treated as such.
    """

    def __new__(cls, msgid, msgtext=None, params=None,
                domain='oslo', *args):
        """Create a new Message object.

        In order for translation to work gettext requires a message ID, this
        msgid will be used as the base unicode text. It is also possible
        for the msgid and the base unicode text to be different by passing
        the msgtext parameter.
        """
        # If the base msgtext is not given, we use the default translation
        # of the msgid (which is in English) just in case the system locale is
        # not English, so that the base text will be in that locale by default.
        if not msgtext:
            msgtext = Message._translate_msgid(msgid, domain)
        # We want to initialize the parent unicode with the actual object that
        # would have been plain unicode if 'Message' was not enabled.
        msg = super(Message, cls).__new__(cls, msgtext)
        msg.msgid = msgid
        msg.domain = domain
        msg.params = params
        return msg

    def translate(self, desired_locale=None):
        """Translate this message to the desired locale.

        :param desired_locale: The desired locale to translate the message to,
                               if no locale is provided the message will be
                               translated to the system's default locale.

        :returns: the translated message in unicode
        """

        translated_message = Message._translate_msgid(self.msgid,
                                                      self.domain,
                                                      desired_locale)
        if self.params is None:
            # No need for more translation
            return translated_message

        # This Message object may have been formatted with one or more
        # Message objects as substitution arguments, given either as a single
        # argument, part of a tuple, or as one or more values in a dictionary.
        # When translating this Message we need to translate those Messages too
        translated_params = _translate.translate_args(self.params,
                                                      desired_locale)

        translated_message = translated_message % translated_params

        return translated_message

    @staticmethod
    def _translate_msgid(msgid, domain, desired_locale=None):
        if not desired_locale:
            system_locale = locale.getdefaultlocale()
            # If the system locale is not available to the runtime use English
            desired_locale = system_locale[0] or 'en_US'

        locale_dir = os.environ.get(
            _locale.get_locale_dir_variable_name(domain)
        )
        lang = gettext.translation(domain,
                                   localedir=locale_dir,
                                   languages=[desired_locale],
                                   fallback=True)
        translator = lang.gettext if six.PY3 else lang.ugettext

        translated_message = translator(msgid)
        return translated_message

    def __mod__(self, other):
        # When we mod a Message we want the actual operation to be performed
        # by the parent class (i.e. unicode()), the only thing  we do here is
        # save the original msgid and the parameters in case of a translation
        params = self._sanitize_mod_params(other)
        unicode_mod = super(Message, self).__mod__(params)
        modded = Message(self.msgid,
                         msgtext=unicode_mod,
                         params=params,
                         domain=self.domain)
        return modded

    def _sanitize_mod_params(self, other):
        """Sanitize the object being modded with this Message.

        - Add support for modding 'None' so translation supports it
        - Trim the modded object, which can be a large dictionary, to only
        those keys that would actually be used in a translation
        - Snapshot the object being modded, in case the message is
        translated, it will be used as it was when the Message was created
        """
        if other is None:
            params = (other,)
        elif isinstance(other, dict):
            # Merge the dictionaries
            # Copy each item in case one does not support deep copy.
            params = {}
            if isinstance(self.params, dict):
                params.update((key, self._copy_param(val))
                              for key, val in self.params.items())
            params.update((key, self._copy_param(val))
                          for key, val in other.items())
        else:
            params = self._copy_param(other)
        return params

    def _copy_param(self, param):
        try:
            return copy.deepcopy(param)
        except Exception:
            # Fallback to casting to unicode this will handle the
            # python code-like objects that can't be deep-copied
            return six.text_type(param)

    def __add__(self, other):
        from oslo_i18n._i18n import _
        msg = _('Message objects do not support addition.')
        raise TypeError(msg)

    def __radd__(self, other):
        return self.__add__(other)

    if six.PY2:
        def __str__(self):
            # NOTE(luisg): Logging in python 2.6 tries to str() log records,
            # and it expects specifically a UnicodeError in order to proceed.
            from oslo_i18n._i18n import _
            msg = _('Message objects do not support str() because they may '
                    'contain non-ascii characters. '
                    'Please use unicode() or translate() instead.')
            raise UnicodeError(msg)

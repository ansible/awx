# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

"""
gettext for openstack-common modules.

Usual usage in an openstack.common module:

    from troveclient.openstack.common.gettextutils import _
"""

import copy
import gettext
import logging
import os
import re
try:
    import UserString as _userString
except ImportError:
    import collections as _userString

from babel import localedata
import six

_localedir = os.environ.get('troveclient'.upper() + '_LOCALEDIR')
_t = gettext.translation('troveclient', localedir=_localedir, fallback=True)

_AVAILABLE_LANGUAGES = {}
USE_LAZY = False


def enable_lazy():
    """Convenience function for configuring _() to use lazy gettext

    Call this at the start of execution to enable the gettextutils._
    function to use lazy gettext functionality. This is useful if
    your project is importing _ directly instead of using the
    gettextutils.install() way of importing the _ function.
    """
    global USE_LAZY
    USE_LAZY = True


def _(msg):
    if USE_LAZY:
        return Message(msg, 'troveclient')
    else:
        if six.PY3:
            return _t.gettext(msg)
        return _t.ugettext(msg)


def install(domain, lazy=False):
    """Install a _() function using the given translation domain.

    Given a translation domain, install a _() function using gettext's
    install() function.

    The main difference from gettext.install() is that we allow
    overriding the default localedir (e.g. /usr/share/locale) using
    a translation-domain-specific environment variable (e.g.
    NOVA_LOCALEDIR).

    :param domain: the translation domain
    :param lazy: indicates whether or not to install the lazy _() function.
                 The lazy _() introduces a way to do deferred translation
                 of messages by installing a _ that builds Message objects,
                 instead of strings, which can then be lazily translated into
                 any available locale.
    """
    if lazy:
        # NOTE(mrodden): Lazy gettext functionality.
        #
        # The following introduces a deferred way to do translations on
        # messages in OpenStack. We override the standard _() function
        # and % (format string) operation to build Message objects that can
        # later be translated when we have more information.
        #
        # Also included below is an example LocaleHandler that translates
        # Messages to an associated locale, effectively allowing many logs,
        # each with their own locale.

        def _lazy_gettext(msg):
            """Create and return a Message object.

            Lazy gettext function for a given domain, it is a factory method
            for a project/module to get a lazy gettext function for its own
            translation domain (i.e. nova, glance, cinder, etc.)

            Message encapsulates a string so that we can translate
            it later when needed.
            """
            return Message(msg, domain)

        from six import moves
        moves.builtins.__dict__['_'] = _lazy_gettext
    else:
        localedir = '%s_LOCALEDIR' % domain.upper()
        if six.PY3:
            gettext.install(domain,
                            localedir=os.environ.get(localedir))
        else:
            gettext.install(domain,
                            localedir=os.environ.get(localedir),
                            unicode=True)


class Message(_userString.UserString, object):
    """Class used to encapsulate translatable messages."""
    def __init__(self, msg, domain):
        # _msg is the gettext msgid and should never change
        self._msg = msg
        self._left_extra_msg = ''
        self._right_extra_msg = ''
        self._locale = None
        self.params = None
        self.domain = domain

    @property
    def data(self):
        # NOTE(mrodden): this should always resolve to a unicode string
        # that best represents the state of the message currently

        localedir = os.environ.get(self.domain.upper() + '_LOCALEDIR')
        if self.locale:
            lang = gettext.translation(self.domain,
                                       localedir=localedir,
                                       languages=[self.locale],
                                       fallback=True)
        else:
            # use system locale for translations
            lang = gettext.translation(self.domain,
                                       localedir=localedir,
                                       fallback=True)

        if six.PY3:
            ugettext = lang.gettext
        else:
            ugettext = lang.ugettext

        full_msg = (self._left_extra_msg +
                    ugettext(self._msg) +
                    self._right_extra_msg)

        if self.params is not None:
            full_msg = full_msg % self.params

        return six.text_type(full_msg)

    @property
    def locale(self):
        return self._locale

    @locale.setter
    def locale(self, value):
        self._locale = value
        if not self.params:
            return

        # This Message object may have been constructed with one or more
        # Message objects as substitution parameters, given as a single
        # Message, or a tuple or Map containing some, so when setting the
        # locale for this Message we need to set it for those Messages too.
        if isinstance(self.params, Message):
            self.params.locale = value
            return
        if isinstance(self.params, tuple):
            for param in self.params:
                if isinstance(param, Message):
                    param.locale = value
            return
        for param in self.params.values():
            if isinstance(param, Message):
                param.locale = value

    def _save_dictionary_parameter(self, dict_param):
        full_msg = self.data
        # look for %(blah) fields in string;
        # ignore %% and deal with the
        # case where % is first character on the line
        keys = re.findall('(?:[^%]|^)?%\((\w*)\)[a-z]', full_msg)

        # if we don't find any %(blah) blocks but have a %s
        if not keys and re.findall('(?:[^%]|^)%[a-z]', full_msg):
            # apparently the full dictionary is the parameter
            params = copy.deepcopy(dict_param)
        else:
            params = {}
            for key in keys:
                try:
                    params[key] = copy.deepcopy(dict_param[key])
                except TypeError:
                    # cast uncopyable thing to unicode string
                    params[key] = six.text_type(dict_param[key])

        return params

    def _save_parameters(self, other):
        # we check for None later to see if
        # we actually have parameters to inject,
        # so encapsulate if our parameter is actually None
        if other is None:
            self.params = (other, )
        elif isinstance(other, dict):
            self.params = self._save_dictionary_parameter(other)
        else:
            # fallback to casting to unicode,
            # this will handle the problematic python code-like
            # objects that cannot be deep-copied
            try:
                self.params = copy.deepcopy(other)
            except TypeError:
                self.params = six.text_type(other)

        return self

    # overrides to be more string-like
    def __unicode__(self):
        return self.data

    def __str__(self):
        if six.PY3:
            return self.__unicode__()
        return self.data.encode('utf-8')

    def __getstate__(self):
        to_copy = ['_msg', '_right_extra_msg', '_left_extra_msg',
                   'domain', 'params', '_locale']
        new_dict = self.__dict__.fromkeys(to_copy)
        for attr in to_copy:
            new_dict[attr] = copy.deepcopy(self.__dict__[attr])

        return new_dict

    def __setstate__(self, state):
        for (k, v) in state.items():
            setattr(self, k, v)

    # operator overloads
    def __add__(self, other):
        copied = copy.deepcopy(self)
        copied._right_extra_msg += other.__str__()
        return copied

    def __radd__(self, other):
        copied = copy.deepcopy(self)
        copied._left_extra_msg += other.__str__()
        return copied

    def __mod__(self, other):
        # do a format string to catch and raise
        # any possible KeyErrors from missing parameters
        self.data % other
        copied = copy.deepcopy(self)
        return copied._save_parameters(other)

    def __mul__(self, other):
        return self.data * other

    def __rmul__(self, other):
        return other * self.data

    def __getitem__(self, key):
        return self.data[key]

    def __getslice__(self, start, end):
        return self.data.__getslice__(start, end)

    def __getattribute__(self, name):
        # NOTE(mrodden): handle lossy operations that we can't deal with yet
        # These override the UserString implementation, since UserString
        # uses our __class__ attribute to try and build a new message
        # after running the inner data string through the operation.
        # At that point, we have lost the gettext message id and can just
        # safely resolve to a string instead.
        ops = ['capitalize', 'center', 'decode', 'encode',
               'expandtabs', 'ljust', 'lstrip', 'replace', 'rjust', 'rstrip',
               'strip', 'swapcase', 'title', 'translate', 'upper', 'zfill']
        if name in ops:
            return getattr(self.data, name)
        else:
            return _userString.UserString.__getattribute__(self, name)


def get_available_languages(domain):
    """Lists the available languages for the given translation domain.

    :param domain: the domain to get languages for
    """
    if domain in _AVAILABLE_LANGUAGES:
        return copy.copy(_AVAILABLE_LANGUAGES[domain])

    localedir = '%s_LOCALEDIR' % domain.upper()
    find = lambda x: gettext.find(domain,
                                  localedir=os.environ.get(localedir),
                                  languages=[x])

    # NOTE(mrodden): en_US should always be available (and first in case
    # order matters) since our in-line message strings are en_US
    language_list = ['en_US']
    # NOTE(luisg): Babel <1.0 used a function called list(), which was
    # renamed to locale_identifiers() in >=1.0, the requirements master list
    # requires >=0.9.6, uncapped, so defensively work with both. We can remove
    # this check when the master list updates to >=1.0, and all projects udpate
    list_identifiers = (getattr(localedata, 'list', None) or
                        getattr(localedata, 'locale_identifiers'))
    locale_identifiers = list_identifiers()
    for i in locale_identifiers:
        if find(i) is not None:
            language_list.append(i)
    _AVAILABLE_LANGUAGES[domain] = language_list
    return copy.copy(language_list)


def get_localized_message(message, user_locale):
    """Gets a localized version of the given message in the given locale."""
    if isinstance(message, Message):
        if user_locale:
            message.locale = user_locale
        return six.text_type(message)
    else:
        return message


class LocaleHandler(logging.Handler):
    """Handler that can have a locale associated to translate Messages.

    A quick example of how to utilize the Message class above.
    LocaleHandler takes a locale and a target logging.Handler object
    to forward LogRecord objects to after translating the internal Message.
    """

    def __init__(self, locale, target):
        """Initialize a LocaleHandler

        :param locale: locale to use for translating messages
        :param target: logging.Handler object to forward
                       LogRecord objects to after translation
        """
        logging.Handler.__init__(self)
        self.locale = locale
        self.target = target

    def emit(self, record):
        if isinstance(record.msg, Message):
            # set the locale and resolve to a string
            record.msg.locale = self.locale

        self.target.emit(record)

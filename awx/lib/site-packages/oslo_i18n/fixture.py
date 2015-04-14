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
"""Test fixtures for working with oslo_i18n.

"""

import gettext

import fixtures
import six

from oslo_i18n import _lazy
from oslo_i18n import _message


class Translation(fixtures.Fixture):
    """Fixture for managing translatable strings.

    This class provides methods for creating translatable strings
    using both lazy translation and immediate translation. It can be
    used to generate the different types of messages returned from
    oslo_i18n to test code that may need to know about the type to
    handle them differently (for example, error handling in WSGI apps,
    or logging).

    Use this class to generate messages instead of toggling the global
    lazy flag and using the regular translation factory.

    """

    def __init__(self, domain='test-domain'):
        """Initialize the fixture.

        :param domain: The translation domain. This is not expected to
                       coincide with an actual set of message
                       catalogs, but it can.
        :type domain: str
        """
        self.domain = domain

    def lazy(self, msg):
        """Return a lazily translated message.

        :param msg: Input message string. May optionally include
                    positional or named string interpolation markers.
        :type msg: str or unicode

        """
        return _message.Message(msg, domain=self.domain)

    def immediate(self, msg):
        """Return a string as though it had been translated immediately.

        :param msg: Input message string. May optionally include
                    positional or named string interpolation markers.
        :type msg: str or unicode

        """
        return six.text_type(msg)


class ToggleLazy(fixtures.Fixture):
    """Fixture to toggle lazy translation on or off for a test."""

    def __init__(self, enabled):
        """Force lazy translation on or off.

        :param enabled: Flag controlling whether to enable or disable
            lazy translation, passed to :func:`~oslo_i18n.enable_lazy`.
        :type enabled: bool
        """
        super(ToggleLazy, self).__init__()
        self._enabled = enabled
        self._original_value = _lazy.USE_LAZY

    def setUp(self):
        super(ToggleLazy, self).setUp()
        self.addCleanup(self._restore_original)
        _lazy.enable_lazy(self._enabled)

    def _restore_original(self):
        _lazy.enable_lazy(self._original_value)


class _PrefixTranslator(gettext.NullTranslations):
    """Translator that adds prefix to message ids

    NOTE: gettext.NullTranslations is an old style class

    :parm prefix: prefix to add to message id.  If not specified (None)
                  then 'noprefix' is used.
    :type prefix: string

    """

    def __init__(self, fp=None, prefix='noprefix'):
        gettext.NullTranslations.__init__(self, fp)
        self.prefix = prefix

    def gettext(self, message):
        msg = gettext.NullTranslations.gettext(self, message)
        return self.prefix + msg

    def ugettext(self, message):
        msg = gettext.NullTranslations.ugettext(self, message)
        return self.prefix + msg


def _prefix_translations(*x, **y):
    """Use message id prefixed with domain and language as translation

    """
    return _PrefixTranslator(prefix=x[0] + '/' + y['languages'][0] + ': ')


class PrefixLazyTranslation(fixtures.Fixture):
    """Fixture to prefix lazy translation enabled messages

    Use of this fixture will cause messages supporting lazy translation to
    be replaced with the message id prefixed with 'domain/language:'.
    For example, 'oslo/en_US: message about something'.  It will also
    override the available languages returned from
    oslo_18n.get_available_languages to the specified languages.

    This will enable tests to ensure that messages were translated lazily
    with the specified language and not immediately with the default language.

    NOTE that this does not work unless lazy translation is enabled, so it
    uses the ToggleLazy fixture to enable lazy translation.

    :param languages: list of languages to support.  If not specified (None)
                      then ['en_US'] is used.
    :type languages: list of strings

    """

    _DEFAULT_LANG = 'en_US'

    def __init__(self, languages=None):
        super(PrefixLazyTranslation, self).__init__()
        self.languages = languages or [PrefixLazyTranslation._DEFAULT_LANG]

    def setUp(self):
        super(PrefixLazyTranslation, self).setUp()
        self.useFixture(ToggleLazy(True))
        self.useFixture(fixtures.MonkeyPatch(
            'oslo_i18n._gettextutils.get_available_languages',
            lambda *x, **y: self.languages))
        self.useFixture(fixtures.MonkeyPatch(
            'oslo.i18n.get_available_languages',
            lambda *x, **y: self.languages))
        self.useFixture(fixtures.MonkeyPatch(
            'oslo_i18n.get_available_languages',
            lambda *x, **y: self.languages))
        self.useFixture(fixtures.MonkeyPatch('gettext.translation',
                                             _prefix_translations))

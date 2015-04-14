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
"""A few tests that use the public API to ensure the imports work.
"""

import unittest

import mock

import oslo_i18n
from oslo_i18n import _lazy


class PublicAPITest(unittest.TestCase):

    def test_create_factory(self):
        oslo_i18n.TranslatorFactory('domain')

    def test_install(self):
        with mock.patch('six.moves.builtins'):
            oslo_i18n.install('domain')

    def test_get_available_languages(self):
        oslo_i18n.get_available_languages('domains')

    def test_toggle_lazy(self):
        original = _lazy.USE_LAZY
        try:
            oslo_i18n.enable_lazy(True)
            oslo_i18n.enable_lazy(False)
        finally:
            oslo_i18n.enable_lazy(original)

    def test_translate(self):
        oslo_i18n.translate(u'string')

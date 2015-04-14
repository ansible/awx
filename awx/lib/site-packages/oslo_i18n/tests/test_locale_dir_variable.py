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
import testscenarios.testcase

from oslo_i18n import _locale


class LocaleDirVariableTest(testscenarios.testcase.WithScenarios,
                            test_base.BaseTestCase):

    scenarios = [
        ('simple', {'domain': 'simple', 'expected': 'SIMPLE_LOCALEDIR'}),
        ('with_dot', {'domain': 'one.two', 'expected': 'ONE_TWO_LOCALEDIR'}),
        ('with_dash', {'domain': 'one-two', 'expected': 'ONE_TWO_LOCALEDIR'}),
    ]

    def test_make_variable_name(self):
        var = _locale.get_locale_dir_variable_name(self.domain)
        self.assertEqual(self.expected, var)

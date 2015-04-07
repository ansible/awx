# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import textwrap

import mock
import pep8
import testtools

from keystoneclient.hacking import checks
from keystoneclient.tests.unit import client_fixtures


class TestCheckOsloNamespaceImports(testtools.TestCase):

    # We are patching pep8 so that only the check under test is actually
    # installed.
    @mock.patch('pep8._checks',
                {'physical_line': {}, 'logical_line': {}, 'tree': {}})
    def run_check(self, code):
        pep8.register_check(checks.check_oslo_namespace_imports)

        lines = textwrap.dedent(code).strip().splitlines(True)

        checker = pep8.Checker(lines=lines)
        checker.check_all()
        checker.report._deferred_print.sort()
        return checker.report._deferred_print

    def assert_has_errors(self, code, expected_errors=None):
        actual_errors = [e[:3] for e in self.run_check(code)]
        self.assertEqual(expected_errors or [], actual_errors)

    def test(self):
        code_ex = self.useFixture(client_fixtures.HackingCode())
        code = code_ex.oslo_namespace_imports['code']
        errors = code_ex.oslo_namespace_imports['expected_errors']
        self.assert_has_errors(code, expected_errors=errors)

# -*- coding: utf-8 -*-
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.

from ironicclient.tests.unit import utils

module_str = 'ironicclient'


class ImportTest(utils.BaseTestCase):

    def check_exported_symbols(self, exported_symbols):
        self.assertIn('client', exported_symbols)
        self.assertIn('exc', exported_symbols)
        self.assertIn('exceptions', exported_symbols)

    def test_import_objects(self):
        module = __import__(module_str)
        exported_symbols = dir(module)
        self.check_exported_symbols(exported_symbols)

    def test_default_import(self):
        default_imports = __import__(module_str, globals(), locals(), ['*'])
        exported_symbols = dir(default_imports)
        self.check_exported_symbols(exported_symbols)

    def test_import__all__(self):
        module = __import__(module_str)
        self.check_exported_symbols(module.__all__)

# (c) 2013, AnsibleWorks
#
# This file is part of Ansible Commander
#
# Ansible Commander is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible Commander is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible Commander.  If not, see <http://www.gnu.org/licenses/>.


import json
import StringIO
import sys
from django.core.management import call_command
from django.core.management.base import CommandError
from lib.main.models import *
from lib.main.tests.base import BaseTest

class BaseCommandTest(BaseTest):
    '''
    Base class for tests that run management commands.
    '''

    def run_command(self, name, *args, **options):
        '''
        Run a management command and capture its stdout/stderr along with any
        exceptions.
        '''
        options.setdefault('verbosity', 1)
        options.setdefault('interactive', False)
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        sys.stdout = StringIO.StringIO()
        sys.stderr = StringIO.StringIO()
        result = None
        try:
            result = call_command(name, *args, **options)
        except Exception, e:
            result = e
        except SystemExit, e:
            result = e
        finally:
            captured_stdout = sys.stdout.getvalue()
            captured_stderr = sys.stderr.getvalue()
            sys.stdout = original_stdout
            sys.stderr = original_stderr
        return result, captured_stdout, captured_stderr

class AcomInventoryTest(BaseCommandTest):
    '''
    Test cases for acom_inventory management command.
    '''

    def setUp(self):
        pass

    def test_without_inventory_id(self):
        result, stdout, stderr = self.run_command('acom_inventory', list=True)
        self.assertTrue(isinstance(result, CommandError))
        self.assertEqual(json.loads(stdout), {})

    def test_with_inventory_id_as_argument(self):
        result, stdout, stderr = self.run_command('acom_inventory', list=True,
                                                  inventory=1)
        self.assertTrue(isinstance(result, CommandError))
        self.assertEqual(json.loads(stdout), {})

    def test_with_inventory_id_in_environment(self):
        pass

    def test_with_invalid_inventory_id(self):
        pass

    
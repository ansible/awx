# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# AWX
from awx.main.tests.base import BaseTest
from command_base import BaseCommandMixin

# Django
from django.core.management.base import CommandError

__all__ = ['UpdatePasswordCommandFunctionalTest']

class UpdatePasswordCommandFunctionalTest(BaseCommandMixin, BaseTest):
    def setUp(self):
        super(UpdatePasswordCommandFunctionalTest, self).setUp()
        self.create_test_license_file()
        self.setup_instances()
        self.setup_users()

    def test_updated_ok(self):
        result, stdout, stderr = self.run_command('update_password', username='admin', password='dingleberry')
        self.assertEqual(stdout, 'Password updated\n')

    def test_same_password(self):
        result, stdout, stderr = self.run_command('update_password', username='admin', password='admin')
        self.assertEqual(stdout, 'Password not updated\n')

    def test_error_username_required(self):
        result, stdout, stderr = self.run_command('update_password', password='foo')
        self.assertIsInstance(result, CommandError)
        self.assertEqual(str(result), 'username required')

    def test_error_password_required(self):
        result, stdout, stderr = self.run_command('update_password', username='admin')
        self.assertIsInstance(result, CommandError)
        self.assertEqual(str(result), 'password required')


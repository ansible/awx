# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

# Python
from datetime import datetime
from dateutil.relativedelta import relativedelta
import mock

#Django
from django.core.management.base import CommandError

# AWX
from awx.main.tests.base import BaseTest
from awx.main.tests.commands.base import BaseCommandMixin

__all__ = ['AgeDeletedCommandFunctionalTest']

class AgeDeletedCommandFunctionalTest(BaseCommandMixin, BaseTest):
    def setUp(self):
        super(AgeDeletedCommandFunctionalTest, self).setUp()
        self.create_test_license_file()
        self.setup_instances()
        self.setup_users()
        self.organization = self.make_organization(self.super_django_user)
        self.credential = self.make_credential()
        self.credential2 = self.make_credential()
        self.credential.mark_inactive(True)
        self.credential2.mark_inactive(True)
        self.credential_active = self.make_credential()
        self.super_django_user.mark_inactive(True)

    def test_default(self):
        result, stdout, stderr = self.run_command('age_deleted')
        self.assertEqual(stdout, 'Aged %d items\n' % 3)

    def test_type(self):
        result, stdout, stderr = self.run_command('age_deleted', type='Credential')
        self.assertEqual(stdout, 'Aged %d items\n' % 2)

    def test_id_type(self):
        result, stdout, stderr = self.run_command('age_deleted', type='Credential', id=self.credential.pk)
        self.assertEqual(stdout, 'Aged %d items\n' % 1)

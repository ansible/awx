# Copyright (c) 2015 Ansible, Inc.

# Python
import mock

# Django
from django.test import SimpleTestCase

# AWX
from awx.main.models import * # noqa
from awx.main.ha import * # noqa

__all__ = ['HAUnitTest',]

class HAUnitTest(SimpleTestCase):

    @mock.patch('awx.main.models.Instance.objects.count', return_value=2)
    def test_multiple_instances(self, ignore):
        self.assertTrue(is_ha_environment())

    @mock.patch('awx.main.models.Instance.objects.count', return_value=1)
    def test_db_localhost(self, ignore):
        self.assertFalse(is_ha_environment())


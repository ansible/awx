# Copyright (c) 2015 Ansible, Inc.

# Python
import mock

# Django
from django.test import SimpleTestCase
from django.conf import settings

# AWX
from awx.main.models import * # noqa
from awx.main.ha import * # noqa
from awx.main.tests.base import BaseTest

__all__ = ['HAUnitTest',]

class HAUnitTest(SimpleTestCase):

    @mock.patch('awx.main.models.Instance.objects.count', return_value=2)
    def test_multiple_instances(self, ignore):
        self.assertTrue(is_ha_environment())

    @mock.patch('awx.main.models.Instance.objects.count', return_value=1)
    @mock.patch.dict('django.conf.settings.DATABASES', { 'HOST': 'localhost' })
    def test_db_localhost(self, ignore):
        self.assertFalse(is_ha_environment())

    @mock.patch('awx.main.models.Instance.objects.count', return_value=1)
    @mock.patch.dict('django.conf.settings.DATABASES', { 'HOST': '127.0.0.1' })
    def test_db_127_0_0_1(self, ignore):
        self.assertFalse(is_ha_environment())

    @mock.patch('awx.main.models.Instance.objects.count', return_value=1)
    @mock.patch.dict('django.conf.settings.DATABASES', { 'HOST': '/i/might/be/a/file' })
    def test_db_file_socket(self, ignore):
        self.assertFalse(is_ha_environment())

# Copyright (c) 2015 Ansible, Inc. (formerly AnsibleWorks, Inc.)

# Python
import mock

# Django
from django.test import SimpleTestCase

# AWX
from awx.main.models import * # noqa
from awx.main.ha import * # noqa

__all__ = ['HAUnitTest',]

TEST_LOCALHOST = {
    'HOST': 'localhost'
}

TEST_127_0_0_1 = {
    'HOST': '127.0.0.1'
} 

TEST_FILE = {
    'HOST': '/i/might/be/a/file',
}

class HAUnitTest(SimpleTestCase):

    @mock.patch('awx.main.models.Instance.objects.count', return_value=2)
    def test_multiple_instances(self, ignore):
        self.assertTrue(is_ha_environment())

    @mock.patch('awx.main.models.Instance.objects.count', return_value=1)
    @mock.patch.dict('django.conf.settings.DATABASES', TEST_LOCALHOST)
    def test_db_localhost(self, ignore):
        self.assertFalse(is_ha_environment())

    @mock.patch('awx.main.models.Instance.objects.count', return_value=1)
    @mock.patch.dict('django.conf.settings.DATABASES', TEST_127_0_0_1)
    def test_db_127_0_0_1(self, ignore):
        self.assertFalse(is_ha_environment())

    @mock.patch('awx.main.models.Instance.objects.count', return_value=1)
    @mock.patch.dict('django.conf.settings.DATABASES', TEST_FILE)
    def test_db_file_socket(self, ignore):
        self.assertFalse(is_ha_environment())

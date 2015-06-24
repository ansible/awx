# Copyright (c) 2015 Ansible, Inc.

# Python
import mock

# Django
from django.test import SimpleTestCase

# AWX
from awx.main.models import * # noqa
from awx.main.ha import * # noqa

__all__ = ['HAUnitTest',]

TEST_LOCALHOST = {
    'default': {
        'HOST': 'localhost'
    }
}

TEST_127_0_0_1 = {
    'default': {
        'HOST': '127.0.0.1'
    }
} 

TEST_FILE = {
    'default': {
        'HOST': '/i/might/be/a/file'
    }
}

TEST_DOMAIN = {
    'default': {
        'HOST': 'postgres.mycompany.com'
    }
}

TEST_REMOTE_IP = {
    'default': {
        'HOST': '8.8.8.8'
    }
}

TEST_EMPTY = {
    'default': {
    }
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

    @mock.patch('awx.main.models.Instance.objects.count', return_value=1)
    @mock.patch.dict('django.conf.settings.DATABASES', TEST_DOMAIN)
    def test_db_domain(self, ignore):
        self.assertTrue(is_ha_environment())

    @mock.patch('awx.main.models.Instance.objects.count', return_value=1)
    @mock.patch.dict('django.conf.settings.DATABASES', TEST_REMOTE_IP)
    def test_db_remote_ip(self, ignore):
        self.assertTrue(is_ha_environment())

    @mock.patch('awx.main.models.Instance.objects.count', return_value=1)
    @mock.patch.dict('django.conf.settings.DATABASES', TEST_EMPTY)
    def test_db_empty(self, ignore):
        self.assertFalse(is_ha_environment())

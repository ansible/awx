from django.conf import settings
from django.core.management import call_command
from django.db.models import loading
from django.db import models
from django.utils import unittest

from django_extensions.db.fields.json import JSONField


class TestModel(models.Model):
    a = models.IntegerField()
    j_field = JSONField()


class JsonFieldTest(unittest.TestCase):
    def setUp(self):
        self.old_installed_apps = settings.INSTALLED_APPS
        settings.INSTALLED_APPS = list(settings.INSTALLED_APPS)
        settings.INSTALLED_APPS.append('django_extensions.tests')
        loading.cache.loaded = False
        call_command('syncdb', verbosity=0)

    def tearDown(self):
        settings.INSTALLED_APPS = self.old_installed_apps

    def testCharFieldCreate(self):
        j = TestModel.objects.create(a=6, j_field=dict(foo='bar'))
        self.assertEqual(j.a, 6)

    def testDefault(self):
        j = TestModel.objects.create(a=1)
        self.assertEqual(j.j_field, {})

    def testEmptyList(self):
        j = TestModel.objects.create(a=6, j_field=[])
        self.assertTrue(isinstance(j.j_field, list))
        self.assertEqual(j.j_field, [])

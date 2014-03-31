from django.db import models

from django_extensions.db.fields.json import JSONField
from django_extensions.tests.fields import FieldTestCase


class TestModel(models.Model):
    a = models.IntegerField()
    j_field = JSONField()


class JsonFieldTest(FieldTestCase):
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

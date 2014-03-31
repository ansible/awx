import six

from django.db import models

from django_extensions.db.fields import UUIDField
from django_extensions.tests.fields import FieldTestCase


class TestModel_field(models.Model):
    a = models.IntegerField()
    uuid_field = UUIDField()


class TestModel_pk(models.Model):
    uuid_field = UUIDField(primary_key=True)


class TestAgregateModel(TestModel_pk):
    a = models.IntegerField()


class TestManyToManyModel(TestModel_pk):
    many = models.ManyToManyField(TestModel_field)


class UUIDFieldTest(FieldTestCase):
    def testUUIDFieldCreate(self):
        j = TestModel_field.objects.create(a=6, uuid_field=six.u('550e8400-e29b-41d4-a716-446655440000'))
        self.assertEqual(j.uuid_field, six.u('550e8400-e29b-41d4-a716-446655440000'))

    def testUUIDField_pkCreate(self):
        j = TestModel_pk.objects.create(uuid_field=six.u('550e8400-e29b-41d4-a716-446655440000'))
        self.assertEqual(j.uuid_field, six.u('550e8400-e29b-41d4-a716-446655440000'))
        self.assertEqual(j.pk, six.u('550e8400-e29b-41d4-a716-446655440000'))

    def testUUIDField_pkAgregateCreate(self):
        j = TestAgregateModel.objects.create(a=6, uuid_field=six.u('550e8400-e29b-41d4-a716-446655440001'))
        self.assertEqual(j.a, 6)
        self.assertIsInstance(j.pk, six.string_types)
        self.assertEqual(len(j.pk), 36)

    def testUUIDFieldManyToManyCreate(self):
        j = TestManyToManyModel.objects.create(uuid_field=six.u('550e8400-e29b-41d4-a716-446655440010'))
        self.assertEqual(j.uuid_field, six.u('550e8400-e29b-41d4-a716-446655440010'))
        self.assertEqual(j.pk, six.u('550e8400-e29b-41d4-a716-446655440010'))


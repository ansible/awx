#:coding=utf-8:
from django.test import TestCase as DjangoTestCase
from django.utils import unittest
from django.utils.encoding import force_text
from django import forms

from jsonfield.tests.jsonfield_test_app.models import *
from jsonfield.fields import JSONField

class JSONFieldTest(DjangoTestCase):
    def test_json_field(self):
        obj = JSONFieldTestModel(json='''{
            "spam": "eggs"
        }''')
        self.assertEquals(obj.json, {'spam':'eggs'})

    def test_json_field_empty(self):
        obj = JSONFieldTestModel(json='')
        self.assertEquals(obj.json, None)

    def test_json_field_save(self):
        JSONFieldTestModel.objects.create(
            id=10,
            json='''{
                "spam": "eggs"
            }''',
        )
        obj2 = JSONFieldTestModel.objects.get(id=10)
        self.assertEquals(obj2.json, {'spam':'eggs'})

    def test_json_field_save_empty(self):
        JSONFieldTestModel.objects.create(id=10, json='')
        obj2 = JSONFieldTestModel.objects.get(id=10)
        self.assertEquals(obj2.json, None)

    def test_db_prep_save(self):
        field = JSONField("test")
        field.set_attributes_from_name("json")
        self.assertEquals(None, field.get_db_prep_save(None, connection=None))
        self.assertEquals('{"spam": "eggs"}', field.get_db_prep_save({"spam": "eggs"}, connection=None))

    def test_formfield(self):
        from jsonfield.forms import JSONFormField
        from jsonfield.widgets import JSONWidget
        field = JSONField("test")
        field.set_attributes_from_name("json")
        formfield = field.formfield()
        self.assertEquals(type(formfield), JSONFormField)
        self.assertEquals(type(formfield.widget), JSONWidget)

    def test_formfield_clean_blank(self):
        field = JSONField("test")
        formfield = field.formfield()
        self.assertRaisesMessage(forms.ValidationError, force_text(formfield.error_messages['required']), formfield.clean, value='')

    def test_formfield_clean_none(self):
        field = JSONField("test")
        formfield = field.formfield()
        self.assertRaisesMessage(forms.ValidationError, force_text(formfield.error_messages['required']), formfield.clean, value=None)

    def test_formfield_null_and_blank_clean_blank(self):
        field = JSONField("test", null=True, blank=True)
        formfield = field.formfield()
        self.assertEquals(formfield.clean(value=''), '')

    def test_formfield_null_and_blank_clean_none(self):
        field = JSONField("test", null=True, blank=True)
        formfield = field.formfield()
        self.assertEquals(formfield.clean(value=None), None)

    def test_formfield_blank_clean_blank(self):
        field = JSONField("test", null=False, blank=True)
        formfield = field.formfield()
        self.assertEquals(formfield.clean(value=''), '')

    def test_formfield_blank_clean_none(self):
        # Hmm, I'm not sure how to do this. What happens if we pass a
        # None to a field that has null=False?
        field = JSONField("test", null=False, blank=True)
        formfield = field.formfield()
        self.assertEquals(formfield.clean(value=None), None)

    def test_default_value(self):
        obj = JSONFieldWithDefaultTestModel.objects.create()
        obj = JSONFieldWithDefaultTestModel.objects.get(id=obj.id)
        self.assertEquals(obj.json, {'sukasuka': 'YAAAAAZ'})

    def test_query_object(self):
        JSONFieldTestModel.objects.create(json={})
        JSONFieldTestModel.objects.create(json={'foo':'bar'})
        self.assertEquals(2, JSONFieldTestModel.objects.all().count())
        self.assertEquals(1, JSONFieldTestModel.objects.exclude(json={}).count())
        self.assertEquals(1, JSONFieldTestModel.objects.filter(json={}).count())
        self.assertEquals(1, JSONFieldTestModel.objects.filter(json={'foo':'bar'}).count())
        self.assertEquals(1, JSONFieldTestModel.objects.filter(json__contains={'foo':'bar'}).count())
        JSONFieldTestModel.objects.create(json={'foo':'bar', 'baz':'bing'})
        self.assertEquals(2, JSONFieldTestModel.objects.filter(json__contains={'foo':'bar'}).count())
        self.assertEquals(1, JSONFieldTestModel.objects.filter(json__contains={'baz':'bing', 'foo':'bar'}).count())
        self.assertEquals(2, JSONFieldTestModel.objects.filter(json__contains='foo').count())
        # This code needs to be implemented!
        self.assertRaises(TypeError, lambda:JSONFieldTestModel.objects.filter(json__contains=['baz', 'foo']))

    def test_query_isnull(self):
        JSONFieldTestModel.objects.create(json=None)
        JSONFieldTestModel.objects.create(json={})
        JSONFieldTestModel.objects.create(json={'foo':'bar'})

        self.assertEquals(1, JSONFieldTestModel.objects.filter(json=None).count())
        self.assertEquals(None, JSONFieldTestModel.objects.get(json=None).json)

    def test_jsonfield_blank(self):
        BlankJSONFieldTestModel.objects.create(blank_json='', null_json=None)
        obj = BlankJSONFieldTestModel.objects.get()
        self.assertEquals(None, obj.null_json)
        self.assertEquals("", obj.blank_json)
        obj.save()
        obj = BlankJSONFieldTestModel.objects.get()
        self.assertEquals(None, obj.null_json)
        self.assertEquals("", obj.blank_json)

    def test_callable_default(self):
        CallableDefaultModel.objects.create()
        obj = CallableDefaultModel.objects.get()
        self.assertEquals({'x':2}, obj.json)

    def test_callable_default_overridden(self):
        CallableDefaultModel.objects.create(json={'x':3})
        obj = CallableDefaultModel.objects.get()
        self.assertEquals({'x':3}, obj.json)

    def test_mutable_default_checking(self):
        obj1 = JSONFieldWithDefaultTestModel()
        obj2 = JSONFieldWithDefaultTestModel()
        
        obj1.json['foo'] = 'bar'
        self.assertNotIn('foo', obj2.json)

    def test_invalid_json(self):
        obj = JSONFieldTestModel()
        obj.json = '{"foo": 2}'
        self.assertIn('foo', obj.json)
        with self.assertRaises(forms.ValidationError):
            obj.json = '{"foo"}'

    def test_invalid_json_default(self):
        with self.assertRaises(ValueError):
            field = JSONField('test', default='{"foo"}')

class SavingModelsTest(DjangoTestCase):
    def test_saving_null(self):
        obj = BlankJSONFieldTestModel.objects.create(blank_json='', null_json=None)
        self.assertEquals('', obj.blank_json)
        self.assertEquals(None, obj.null_json)
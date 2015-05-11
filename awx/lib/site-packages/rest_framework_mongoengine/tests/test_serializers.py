from datetime import datetime 
import mongoengine as me 
from unittest import TestCase
from bson import objectid

from rest_framework_mongoengine.serializers import MongoEngineModelSerializer
from rest_framework import serializers as s


class Job(me.Document):
    title = me.StringField()
    status = me.StringField(choices=('draft', 'published'))
    notes = me.StringField(required=False)
    on = me.DateTimeField(default=datetime.utcnow)
    weight = me.IntField(default=0)


class JobSerializer(MongoEngineModelSerializer):
    id = s.Field()
    title = s.CharField()
    status = s.ChoiceField(read_only=True)
    sort_weight = s.IntegerField(source='weight')


    class Meta:
        model = Job 
        fields = ('id', 'title','status', 'sort_weight')



class TestReadonlyRestore(TestCase):

    def test_restore_object(self):
        job = Job(title='original title', status='draft', notes='secure')
        data = {
            'title': 'updated title ...',
            'status': 'published',  # this one is read only
            'notes': 'hacked', # this field should not update
            'sort_weight': 10 # mapped to a field with differet name
        }

        serializer = JobSerializer(job, data=data, partial=True)

        self.assertTrue(serializer.is_valid())
        obj = serializer.object 
        self.assertEqual(data['title'], obj.title)
        self.assertEqual('draft', obj.status)
        self.assertEqual('secure', obj.notes)

        self.assertEqual(10, obj.weight)





# Testing restoring embedded property 

class Location(me.EmbeddedDocument):
    city = me.StringField()

# list of 
class Category(me.EmbeddedDocument):
    id = me.StringField()
    counter = me.IntField(default=0, required=True)


class Secret(me.EmbeddedDocument):
    key = me.StringField()

class SomeObject(me.Document):
    name = me.StringField()
    loc = me.EmbeddedDocumentField('Location')
    categories = me.ListField(me.EmbeddedDocumentField(Category))
    codes = me.ListField(me.EmbeddedDocumentField(Secret))


class LocationSerializer(MongoEngineModelSerializer):
    city = s.CharField()

    class Meta:
        model = Location

class CategorySerializer(MongoEngineModelSerializer):
    id = s.CharField(max_length=24)
    class Meta:
        model = Category
        fields = ('id',)

class SomeObjectSerializer(MongoEngineModelSerializer):
    location = LocationSerializer(source='loc')
    categories = CategorySerializer(many=True, allow_add_remove=True)

    class Meta:
        model = SomeObject
        fields = ('name', 'location', 'categories')


class TestRestoreEmbedded(TestCase):
    def setUp(self):
        self.data = {
            'name': 'some anme', 
            'location': {
                'city': 'Toronto'
            }, 
            'categories': [{'id': 'cat1'}, {'id': 'category_2', 'counter': 666}], 
            'codes': [{'key': 'mykey1'}]
        }

    def test_restore_new(self):
        serializer = SomeObjectSerializer(data=self.data)    
        self.assertTrue(serializer.is_valid())
        obj = serializer.object 

        self.assertEqual(self.data['name'], obj.name )
        self.assertEqual('Toronto', obj.loc.city )

        self.assertEqual(2, len(obj.categories))
        self.assertEqual('category_2', obj.categories[1].id)
        # counter is not listed in serializer fields, cannot be updated
        self.assertEqual(0, obj.categories[1].counter) 

        # codes are not listed, should not be updatable
        self.assertEqual(0, len(obj.codes))

    def test_restore_update(self):        
        data = self.data
        instance = SomeObject(
            name='original', 
            loc=Location(city="New York"), 
            categories=[Category(id='orig1', counter=777)], 
            codes=[Secret(key='confidential123')]
        )
        serializer = SomeObjectSerializer(instance, data=data, partial=True)
         
        # self.assertTrue(serializer.is_valid())
        if not serializer.is_valid():
            print 'errors: %s' % serializer._errors
            assert False, 'errors'

        obj = serializer.object

        self.assertEqual(data['name'], obj.name )
        self.assertEqual('Toronto', obj.loc.city )

        # codes is not listed, should not be updatable
        self.assertEqual(1, len(obj.codes[0]))
        self.assertEqual('confidential123', obj.codes[0].key) # should keep original val

        self.assertEqual(2, len(obj.categories))
        self.assertEqual('category_2', obj.categories[1].id)
        self.assertEqual(0, obj.categories[1].counter)


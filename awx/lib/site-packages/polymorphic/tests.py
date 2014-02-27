# -*- coding: utf-8 -*-
""" Test Cases
    Please see README.rst or DOCS.rst or http://chrisglass.github.com/django_polymorphic/
"""
from __future__ import print_function
import uuid
import re
from django.db.models.query import QuerySet

from django.test import TestCase
from django.db.models import Q,Count
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.utils import six

from polymorphic import PolymorphicModel, PolymorphicManager, PolymorphicQuerySet
from polymorphic import ShowFieldContent, ShowFieldType, ShowFieldTypeAndContent
from polymorphic.tools_for_tests import UUIDField


class PlainA(models.Model):
    field1 = models.CharField(max_length=10)
class PlainB(PlainA):
    field2 = models.CharField(max_length=10)
class PlainC(PlainB):
    field3 = models.CharField(max_length=10)

class Model2A(ShowFieldType, PolymorphicModel):
    field1 = models.CharField(max_length=10)
class Model2B(Model2A):
    field2 = models.CharField(max_length=10)
class Model2C(Model2B):
    field3 = models.CharField(max_length=10)
class Model2D(Model2C):
    field4 = models.CharField(max_length=10)

class ModelExtraA(ShowFieldTypeAndContent, PolymorphicModel):
    field1 = models.CharField(max_length=10)
class ModelExtraB(ModelExtraA):
    field2 = models.CharField(max_length=10)
class ModelExtraC(ModelExtraB):
    field3 = models.CharField(max_length=10)
class ModelExtraExternal(models.Model):
    topic = models.CharField(max_length=10)

class ModelShow1(ShowFieldType,PolymorphicModel):
    field1 = models.CharField(max_length=10)
    m2m = models.ManyToManyField('self')
class ModelShow2(ShowFieldContent, PolymorphicModel):
    field1 = models.CharField(max_length=10)
    m2m = models.ManyToManyField('self')
class ModelShow3(ShowFieldTypeAndContent, PolymorphicModel):
    field1 = models.CharField(max_length=10)
    m2m = models.ManyToManyField('self')

class ModelShow1_plain(PolymorphicModel):
    field1 = models.CharField(max_length=10)
class ModelShow2_plain(ModelShow1_plain):
    field2 = models.CharField(max_length=10)


class Base(ShowFieldType, PolymorphicModel):
    field_b = models.CharField(max_length=10)
class ModelX(Base):
    field_x = models.CharField(max_length=10)
class ModelY(Base):
    field_y = models.CharField(max_length=10)

class Enhance_Plain(models.Model):
    field_p = models.CharField(max_length=10)
class Enhance_Base(ShowFieldTypeAndContent, PolymorphicModel):
    field_b = models.CharField(max_length=10)
class Enhance_Inherit(Enhance_Base, Enhance_Plain):
    field_i = models.CharField(max_length=10)

class DiamondBase(models.Model):
    field_b = models.CharField(max_length=10)
class DiamondX(DiamondBase):
    field_x = models.CharField(max_length=10)
class DiamondY(DiamondBase):
    field_y = models.CharField(max_length=10)
class DiamondXY(DiamondX, DiamondY):
    pass

class RelationBase(ShowFieldTypeAndContent, PolymorphicModel):
    field_base = models.CharField(max_length=10)
    fk = models.ForeignKey('self', null=True, related_name='relationbase_set')
    m2m = models.ManyToManyField('self')
class RelationA(RelationBase):
    field_a = models.CharField(max_length=10)
class RelationB(RelationBase):
    field_b = models.CharField(max_length=10)
class RelationBC(RelationB):
    field_c = models.CharField(max_length=10)

class RelatingModel(models.Model):
    many2many = models.ManyToManyField(Model2A)

class One2OneRelatingModel(PolymorphicModel):
    one2one = models.OneToOneField(Model2A)
    field1 = models.CharField(max_length=10)

class One2OneRelatingModelDerived(One2OneRelatingModel):
    field2 = models.CharField(max_length=10)

class MyManagerQuerySet(PolymorphicQuerySet):
    def my_queryset_foo(self):
        return self.all()  # Just a method to prove the existance of the custom queryset.

class MyManager(PolymorphicManager):
    queryset_class = MyManagerQuerySet

    def get_query_set(self):
        return super(MyManager, self).get_query_set().order_by('-field1')

class ModelWithMyManager(ShowFieldTypeAndContent, Model2A):
    objects = MyManager()
    field4 = models.CharField(max_length=10)

class MROBase1(ShowFieldType, PolymorphicModel):
    objects = MyManager()
    field1 = models.CharField(max_length=10) # needed as MyManager uses it
class MROBase2(MROBase1):
    pass # Django vanilla inheritance does not inherit MyManager as _default_manager here
class MROBase3(models.Model):
    objects = PolymorphicManager()
class MRODerived(MROBase2, MROBase3):
    pass

class ParentModelWithManager(PolymorphicModel):
    pass
class ChildModelWithManager(PolymorphicModel):
    # Also test whether foreign keys receive the manager:
    fk = models.ForeignKey(ParentModelWithManager, related_name='childmodel_set')
    objects = MyManager()


class PlainMyManagerQuerySet(QuerySet):
    def my_queryset_foo(self):
        return self.all()  # Just a method to prove the existance of the custom queryset.

class PlainMyManager(models.Manager):
    def my_queryset_foo(self):
        return self.get_query_set().my_queryset_foo()

    def get_query_set(self):
        return PlainMyManagerQuerySet(self.model, using=self._db)

class PlainParentModelWithManager(models.Model):
    pass

class PlainChildModelWithManager(models.Model):
    fk = models.ForeignKey(PlainParentModelWithManager, related_name='childmodel_set')
    objects = PlainMyManager()


class MgrInheritA(models.Model):
    mgrA = models.Manager()
    mgrA2 = models.Manager()
    field1 = models.CharField(max_length=10)
class MgrInheritB(MgrInheritA):
    mgrB = models.Manager()
    field2 = models.CharField(max_length=10)
class MgrInheritC(ShowFieldTypeAndContent, MgrInheritB):
    pass

class BlogBase(ShowFieldTypeAndContent, PolymorphicModel):
    name = models.CharField(max_length=10)
class BlogA(BlogBase):
    info = models.CharField(max_length=10)
class BlogB(BlogBase):
    pass
class BlogEntry(ShowFieldTypeAndContent, PolymorphicModel):
    blog = models.ForeignKey(BlogA)
    text = models.CharField(max_length=10)

class BlogEntry_limit_choices_to(ShowFieldTypeAndContent, PolymorphicModel):
    blog = models.ForeignKey(BlogBase)
    text = models.CharField(max_length=10)

class ModelFieldNameTest(ShowFieldType, PolymorphicModel):
    modelfieldnametest = models.CharField(max_length=10)

class InitTestModel(ShowFieldType, PolymorphicModel):
    bar = models.CharField(max_length=100)
    def __init__(self, *args, **kwargs):
        kwargs['bar'] = self.x()
        super(InitTestModel, self).__init__(*args, **kwargs)
class InitTestModelSubclass(InitTestModel):
    def x(self):
        return 'XYZ'

# models from github issue
class Top(PolymorphicModel):
    name = models.CharField(max_length=50)
    class Meta:
        ordering = ('pk',)
class Middle(Top):
    description = models.TextField()
class Bottom(Middle):
    author = models.CharField(max_length=50)

class UUIDProject(ShowFieldTypeAndContent, PolymorphicModel):
        uuid_primary_key = UUIDField(primary_key = True)
        topic = models.CharField(max_length = 30)
class UUIDArtProject(UUIDProject):
        artist = models.CharField(max_length = 30)
class UUIDResearchProject(UUIDProject):
        supervisor = models.CharField(max_length = 30)

class UUIDPlainA(models.Model):
    uuid_primary_key = UUIDField(primary_key = True)
    field1 = models.CharField(max_length=10)
class UUIDPlainB(UUIDPlainA):
    field2 = models.CharField(max_length=10)
class UUIDPlainC(UUIDPlainB):
    field3 = models.CharField(max_length=10)

# base -> proxy
class ProxyBase(PolymorphicModel):
    some_data = models.CharField(max_length=128)
class ProxyChild(ProxyBase):
    class Meta:
        proxy = True

# base -> proxy -> real models
class ProxiedBase(ShowFieldTypeAndContent, PolymorphicModel):
    name = models.CharField(max_length=10)
class ProxyModelBase(ProxiedBase):
    class Meta:
        proxy = True
class ProxyModelA(ProxyModelBase):
    field1 = models.CharField(max_length=10)
class ProxyModelB(ProxyModelBase):
    field2 = models.CharField(max_length=10)


# test bad field name
#class TestBadFieldModel(ShowFieldType, PolymorphicModel):
#    instance_of = models.CharField(max_length=10)

# validation error: "polymorphic.relatednameclash: Accessor for field 'polymorphic_ctype' clashes
# with related field 'ContentType.relatednameclash_set'." (reported by Andrew Ingram)
# fixed with related_name
class RelatedNameClash(ShowFieldType, PolymorphicModel):
    ctype = models.ForeignKey(ContentType, null=True, editable=False)


class PolymorphicTests(TestCase):
    """
    The test suite
    """
    def test_diamond_inheritance(self):
        # Django diamond problem
        # https://code.djangoproject.com/ticket/10808
        o1 = DiamondXY.objects.create(field_b='b', field_x='x', field_y='y')
        o2 = DiamondXY.objects.get()

        if o2.field_b != 'b':
            print('')
            print('# known django model inheritance diamond problem detected')
            print('DiamondXY fields 1: field_b "{0}", field_x "{1}", field_y "{2}"'.format(o1.field_b, o1.field_x, o1.field_y))
            print('DiamondXY fields 2: field_b "{0}", field_x "{1}", field_y "{2}"'.format(o2.field_b, o2.field_x, o2.field_y))


    def test_annotate_aggregate_order(self):
        # create a blog of type BlogA
        # create two blog entries in BlogA
        # create some blogs of type BlogB to make the BlogBase table data really polymorphic
        blog = BlogA.objects.create(name='B1', info='i1')
        blog.blogentry_set.create(text='bla')
        BlogEntry.objects.create(blog=blog, text='bla2')
        BlogB.objects.create(name='Bb1')
        BlogB.objects.create(name='Bb2')
        BlogB.objects.create(name='Bb3')

        qs = BlogBase.objects.annotate(entrycount=Count('BlogA___blogentry'))
        self.assertEqual(len(qs), 4)

        for o in qs:
            if o.name == 'B1':
                self.assertEqual(o.entrycount, 2)
            else:
                self.assertEqual(o.entrycount, 0)

        x = BlogBase.objects.aggregate(entrycount=Count('BlogA___blogentry'))
        self.assertEqual(x['entrycount'], 2)

        # create some more blogs for next test
        BlogA.objects.create(name='B2', info='i2')
        BlogA.objects.create(name='B3', info='i3')
        BlogA.objects.create(name='B4', info='i4')
        BlogA.objects.create(name='B5', info='i5')

        # test ordering for field in all entries
        expected = '''
[ <BlogB: id 4, name (CharField) "Bb3">,
  <BlogB: id 3, name (CharField) "Bb2">,
  <BlogB: id 2, name (CharField) "Bb1">,
  <BlogA: id 8, name (CharField) "B5", info (CharField) "i5">,
  <BlogA: id 7, name (CharField) "B4", info (CharField) "i4">,
  <BlogA: id 6, name (CharField) "B3", info (CharField) "i3">,
  <BlogA: id 5, name (CharField) "B2", info (CharField) "i2">,
  <BlogA: id 1, name (CharField) "B1", info (CharField) "i1"> ]'''
        x = '\n' + repr(BlogBase.objects.order_by('-name'))
        self.assertEqual(x, expected)

        # test ordering for field in one subclass only
        # MySQL and SQLite return this order
        expected1='''
[ <BlogA: id 8, name (CharField) "B5", info (CharField) "i5">,
  <BlogA: id 7, name (CharField) "B4", info (CharField) "i4">,
  <BlogA: id 6, name (CharField) "B3", info (CharField) "i3">,
  <BlogA: id 5, name (CharField) "B2", info (CharField) "i2">,
  <BlogA: id 1, name (CharField) "B1", info (CharField) "i1">,
  <BlogB: id 2, name (CharField) "Bb1">,
  <BlogB: id 3, name (CharField) "Bb2">,
  <BlogB: id 4, name (CharField) "Bb3"> ]'''

        # PostgreSQL returns this order
        expected2='''
[ <BlogB: id 2, name (CharField) "Bb1">,
  <BlogB: id 3, name (CharField) "Bb2">,
  <BlogB: id 4, name (CharField) "Bb3">,
  <BlogA: id 8, name (CharField) "B5", info (CharField) "i5">,
  <BlogA: id 7, name (CharField) "B4", info (CharField) "i4">,
  <BlogA: id 6, name (CharField) "B3", info (CharField) "i3">,
  <BlogA: id 5, name (CharField) "B2", info (CharField) "i2">,
  <BlogA: id 1, name (CharField) "B1", info (CharField) "i1"> ]'''

        x = '\n' + repr(BlogBase.objects.order_by('-BlogA___info'))
        self.assertTrue(x == expected1 or x == expected2)


    def test_limit_choices_to(self):
        """
        this is not really a testcase, as limit_choices_to only affects the Django admin
        """
        # create a blog of type BlogA
        blog_a = BlogA.objects.create(name='aa', info='aa')
        blog_b = BlogB.objects.create(name='bb')
        # create two blog entries
        entry1 = BlogEntry_limit_choices_to.objects.create(blog=blog_b, text='bla2')
        entry2 = BlogEntry_limit_choices_to.objects.create(blog=blog_b, text='bla2')


    def test_primary_key_custom_field_problem(self):
        """
        object retrieval problem occuring with some custom primary key fields (UUIDField as test case)
        """
        UUIDProject.objects.create(topic="John's gathering")
        UUIDArtProject.objects.create(topic="Sculpting with Tim", artist="T. Turner")
        UUIDResearchProject.objects.create(topic="Swallow Aerodynamics", supervisor="Dr. Winter")

        qs = UUIDProject.objects.all()
        ol = list(qs)
        a = qs[0]
        b = qs[1]
        c = qs[2]
        self.assertEqual(len(qs), 3)
        self.assertIsInstance(a.uuid_primary_key, uuid.UUID)
        self.assertIsInstance(a.pk, uuid.UUID)

        res = re.sub(' "(.*?)..", topic',', topic', repr(qs))
        res_exp = """[ <UUIDProject: uuid_primary_key (UUIDField/pk), topic (CharField) "John's gathering">,
  <UUIDArtProject: uuid_primary_key (UUIDField/pk), topic (CharField) "Sculpting with Tim", artist (CharField) "T. Turner">,
  <UUIDResearchProject: uuid_primary_key (UUIDField/pk), topic (CharField) "Swallow Aerodynamics", supervisor (CharField) "Dr. Winter"> ]"""
        self.assertEqual(res, res_exp)
        #if (a.pk!= uuid.UUID or c.pk!= uuid.UUID):
        #    print()
        #    print('# known inconstency with custom primary key field detected (django problem?)')

        a = UUIDPlainA.objects.create(field1='A1')
        b = UUIDPlainB.objects.create(field1='B1', field2='B2')
        c = UUIDPlainC.objects.create(field1='C1', field2='C2', field3='C3')
        qs = UUIDPlainA.objects.all()
        if a.pk!= uuid.UUID or c.pk!= uuid.UUID:
            print('')
            print('# known type inconstency with custom primary key field detected (django problem?)')


    def create_model2abcd(self):
        """
        Create the chain of objects of Model2,
        this is reused in various tests.
        """
        Model2A.objects.create(field1='A1')
        Model2B.objects.create(field1='B1', field2='B2')
        Model2C.objects.create(field1='C1', field2='C2', field3='C3')
        Model2D.objects.create(field1='D1', field2='D2', field3='D3', field4='D4')


    def test_simple_inheritance(self):
        self.create_model2abcd()

        objects = list(Model2A.objects.all())
        self.assertEqual(repr(objects[0]), '<Model2A: id 1, field1 (CharField)>')
        self.assertEqual(repr(objects[1]), '<Model2B: id 2, field1 (CharField), field2 (CharField)>')
        self.assertEqual(repr(objects[2]), '<Model2C: id 3, field1 (CharField), field2 (CharField), field3 (CharField)>')
        self.assertEqual(repr(objects[3]), '<Model2D: id 4, field1 (CharField), field2 (CharField), field3 (CharField), field4 (CharField)>')


    def test_manual_get_real_instance(self):
        self.create_model2abcd()

        o = Model2A.objects.non_polymorphic().get(field1='C1')
        self.assertEqual(repr(o.get_real_instance()), '<Model2C: id 3, field1 (CharField), field2 (CharField), field3 (CharField)>')


    def test_non_polymorphic(self):
        self.create_model2abcd()

        objects = list(Model2A.objects.all().non_polymorphic())
        self.assertEqual(repr(objects[0]), '<Model2A: id 1, field1 (CharField)>')
        self.assertEqual(repr(objects[1]), '<Model2A: id 2, field1 (CharField)>')
        self.assertEqual(repr(objects[2]), '<Model2A: id 3, field1 (CharField)>')
        self.assertEqual(repr(objects[3]), '<Model2A: id 4, field1 (CharField)>')


    def test_get_real_instances(self):
        self.create_model2abcd()
        qs = Model2A.objects.all().non_polymorphic()

        # from queryset
        objects = qs.get_real_instances()
        self.assertEqual(repr(objects[0]), '<Model2A: id 1, field1 (CharField)>')
        self.assertEqual(repr(objects[1]), '<Model2B: id 2, field1 (CharField), field2 (CharField)>')
        self.assertEqual(repr(objects[2]), '<Model2C: id 3, field1 (CharField), field2 (CharField), field3 (CharField)>')
        self.assertEqual(repr(objects[3]), '<Model2D: id 4, field1 (CharField), field2 (CharField), field3 (CharField), field4 (CharField)>')

        # from a manual list
        objects = Model2A.objects.get_real_instances(list(qs))
        self.assertEqual(repr(objects[0]), '<Model2A: id 1, field1 (CharField)>')
        self.assertEqual(repr(objects[1]), '<Model2B: id 2, field1 (CharField), field2 (CharField)>')
        self.assertEqual(repr(objects[2]), '<Model2C: id 3, field1 (CharField), field2 (CharField), field3 (CharField)>')
        self.assertEqual(repr(objects[3]), '<Model2D: id 4, field1 (CharField), field2 (CharField), field3 (CharField), field4 (CharField)>')


    def test_translate_polymorphic_q_object(self):
        self.create_model2abcd()

        q = Model2A.translate_polymorphic_Q_object(Q(instance_of=Model2C))
        objects = Model2A.objects.filter(q)
        self.assertEqual(repr(objects[0]), '<Model2C: id 3, field1 (CharField), field2 (CharField), field3 (CharField)>')
        self.assertEqual(repr(objects[1]), '<Model2D: id 4, field1 (CharField), field2 (CharField), field3 (CharField), field4 (CharField)>')


    def test_base_manager(self):
        def show_base_manager(model):
            return "{0} {1}".format(
                repr(type(model._base_manager)),
                repr(model._base_manager.model)
            )

        self.assertEqual(show_base_manager(PlainA), "<class 'django.db.models.manager.Manager'> <class 'polymorphic.tests.PlainA'>")
        self.assertEqual(show_base_manager(PlainB), "<class 'django.db.models.manager.Manager'> <class 'polymorphic.tests.PlainB'>")
        self.assertEqual(show_base_manager(PlainC), "<class 'django.db.models.manager.Manager'> <class 'polymorphic.tests.PlainC'>")

        self.assertEqual(show_base_manager(Model2A), "<class 'polymorphic.manager.PolymorphicManager'> <class 'polymorphic.tests.Model2A'>")
        self.assertEqual(show_base_manager(Model2B), "<class 'django.db.models.manager.Manager'> <class 'polymorphic.tests.Model2B'>")
        self.assertEqual(show_base_manager(Model2C), "<class 'django.db.models.manager.Manager'> <class 'polymorphic.tests.Model2C'>")

        self.assertEqual(show_base_manager(One2OneRelatingModel), "<class 'polymorphic.manager.PolymorphicManager'> <class 'polymorphic.tests.One2OneRelatingModel'>")
        self.assertEqual(show_base_manager(One2OneRelatingModelDerived), "<class 'django.db.models.manager.Manager'> <class 'polymorphic.tests.One2OneRelatingModelDerived'>")


    def test_foreignkey_field(self):
        self.create_model2abcd()

        object2a = Model2A.base_objects.get(field1='C1')
        self.assertEqual(repr(object2a.model2b), '<Model2B: id 3, field1 (CharField), field2 (CharField)>')

        object2b = Model2B.base_objects.get(field1='C1')
        self.assertEqual(repr(object2b.model2c), '<Model2C: id 3, field1 (CharField), field2 (CharField), field3 (CharField)>')


    def test_onetoone_field(self):
        self.create_model2abcd()

        a = Model2A.base_objects.get(field1='C1')
        b = One2OneRelatingModelDerived.objects.create(one2one=a, field1='f1', field2='f2')

        # this result is basically wrong, probably due to Django cacheing (we used base_objects), but should not be a problem
        self.assertEqual(repr(b.one2one), '<Model2A: id 3, field1 (CharField)>')

        c = One2OneRelatingModelDerived.objects.get(field1='f1')
        self.assertEqual(repr(c.one2one), '<Model2C: id 3, field1 (CharField), field2 (CharField), field3 (CharField)>')
        self.assertEqual(repr(a.one2onerelatingmodel), '<One2OneRelatingModelDerived: One2OneRelatingModelDerived object>')


    def test_manytomany_field(self):
        # Model 1
        o = ModelShow1.objects.create(field1='abc')
        o.m2m.add(o)
        o.save()
        self.assertEqual(repr(ModelShow1.objects.all()), '[ <ModelShow1: id 1, field1 (CharField), m2m (ManyToManyField)> ]')

        # Model 2
        o = ModelShow2.objects.create(field1='abc')
        o.m2m.add(o)
        o.save()
        self.assertEqual(repr(ModelShow2.objects.all()), '[ <ModelShow2: id 1, field1 "abc", m2m 1> ]')

        # Model 3
        o=ModelShow3.objects.create(field1='abc')
        o.m2m.add(o)
        o.save()
        self.assertEqual(repr(ModelShow3.objects.all()), '[ <ModelShow3: id 1, field1 (CharField) "abc", m2m (ManyToManyField) 1> ]')
        self.assertEqual(repr(ModelShow1.objects.all().annotate(Count('m2m'))), '[ <ModelShow1: id 1, field1 (CharField), m2m (ManyToManyField) - Ann: m2m__count (int)> ]')
        self.assertEqual(repr(ModelShow2.objects.all().annotate(Count('m2m'))), '[ <ModelShow2: id 1, field1 "abc", m2m 1 - Ann: m2m__count 1> ]')
        self.assertEqual(repr(ModelShow3.objects.all().annotate(Count('m2m'))), '[ <ModelShow3: id 1, field1 (CharField) "abc", m2m (ManyToManyField) 1 - Ann: m2m__count (int) 1> ]')

        # no pretty printing
        ModelShow1_plain.objects.create(field1='abc')
        ModelShow2_plain.objects.create(field1='abc', field2='def')
        self.assertEqual(repr(ModelShow1_plain.objects.all()), '[<ModelShow1_plain: ModelShow1_plain object>, <ModelShow2_plain: ModelShow2_plain object>]')


    def test_extra_method(self):
        self.create_model2abcd()

        objects = list(Model2A.objects.extra(where=['id IN (2, 3)']))
        self.assertEqual(repr(objects[0]), '<Model2B: id 2, field1 (CharField), field2 (CharField)>')
        self.assertEqual(repr(objects[1]), '<Model2C: id 3, field1 (CharField), field2 (CharField), field3 (CharField)>')

        objects = Model2A.objects.extra(select={"select_test": "field1 = 'A1'"}, where=["field1 = 'A1' OR field1 = 'B1'"], order_by=['-id'])
        self.assertEqual(repr(objects[0]), '<Model2B: id 2, field1 (CharField), field2 (CharField) - Extra: select_test (int)>')
        self.assertEqual(repr(objects[1]), '<Model2A: id 1, field1 (CharField) - Extra: select_test (int)>')
        self.assertEqual(len(objects), 2)   # Placed after the other tests, only verifying whether there are no more additional objects.

        ModelExtraA.objects.create(field1='A1')
        ModelExtraB.objects.create(field1='B1', field2='B2')
        ModelExtraC.objects.create(field1='C1', field2='C2', field3='C3')
        ModelExtraExternal.objects.create(topic='extra1')
        ModelExtraExternal.objects.create(topic='extra2')
        ModelExtraExternal.objects.create(topic='extra3')
        objects = ModelExtraA.objects.extra(tables=["polymorphic_modelextraexternal"], select={"topic":"polymorphic_modelextraexternal.topic"}, where=["polymorphic_modelextraa.id = polymorphic_modelextraexternal.id"])
        if six.PY3:
            self.assertEqual(repr(objects[0]), '<ModelExtraA: id 1, field1 (CharField) "A1" - Extra: topic (str) "extra1">')
            self.assertEqual(repr(objects[1]), '<ModelExtraB: id 2, field1 (CharField) "B1", field2 (CharField) "B2" - Extra: topic (str) "extra2">')
            self.assertEqual(repr(objects[2]), '<ModelExtraC: id 3, field1 (CharField) "C1", field2 (CharField) "C2", field3 (CharField) "C3" - Extra: topic (str) "extra3">')
        else:
            self.assertEqual(repr(objects[0]), '<ModelExtraA: id 1, field1 (CharField) "A1" - Extra: topic (unicode) "extra1">')
            self.assertEqual(repr(objects[1]), '<ModelExtraB: id 2, field1 (CharField) "B1", field2 (CharField) "B2" - Extra: topic (unicode) "extra2">')
            self.assertEqual(repr(objects[2]), '<ModelExtraC: id 3, field1 (CharField) "C1", field2 (CharField) "C2", field3 (CharField) "C3" - Extra: topic (unicode) "extra3">')
        self.assertEqual(len(objects), 3)


    def test_instance_of_filter(self):
        self.create_model2abcd()

        objects = Model2A.objects.instance_of(Model2B)
        self.assertEqual(repr(objects[0]), '<Model2B: id 2, field1 (CharField), field2 (CharField)>')
        self.assertEqual(repr(objects[1]), '<Model2C: id 3, field1 (CharField), field2 (CharField), field3 (CharField)>')
        self.assertEqual(repr(objects[2]), '<Model2D: id 4, field1 (CharField), field2 (CharField), field3 (CharField), field4 (CharField)>')
        self.assertEqual(len(objects), 3)

        objects = Model2A.objects.filter(instance_of=Model2B)
        self.assertEqual(repr(objects[0]), '<Model2B: id 2, field1 (CharField), field2 (CharField)>')
        self.assertEqual(repr(objects[1]), '<Model2C: id 3, field1 (CharField), field2 (CharField), field3 (CharField)>')
        self.assertEqual(repr(objects[2]), '<Model2D: id 4, field1 (CharField), field2 (CharField), field3 (CharField), field4 (CharField)>')
        self.assertEqual(len(objects), 3)

        objects = Model2A.objects.filter(Q(instance_of=Model2B))
        self.assertEqual(repr(objects[0]), '<Model2B: id 2, field1 (CharField), field2 (CharField)>')
        self.assertEqual(repr(objects[1]), '<Model2C: id 3, field1 (CharField), field2 (CharField), field3 (CharField)>')
        self.assertEqual(repr(objects[2]), '<Model2D: id 4, field1 (CharField), field2 (CharField), field3 (CharField), field4 (CharField)>')
        self.assertEqual(len(objects), 3)

        objects = Model2A.objects.not_instance_of(Model2B)
        self.assertEqual(repr(objects[0]), '<Model2A: id 1, field1 (CharField)>')
        self.assertEqual(len(objects), 1)


    def test_polymorphic___filter(self):
        self.create_model2abcd()

        objects = Model2A.objects.filter(Q( Model2B___field2='B2') | Q( Model2C___field3='C3'))
        self.assertEqual(len(objects), 2)
        self.assertEqual(repr(objects[0]), '<Model2B: id 2, field1 (CharField), field2 (CharField)>')
        self.assertEqual(repr(objects[1]), '<Model2C: id 3, field1 (CharField), field2 (CharField), field3 (CharField)>')


    def test_delete(self):
        self.create_model2abcd()

        oa = Model2A.objects.get(id=2)
        self.assertEqual(repr(oa), '<Model2B: id 2, field1 (CharField), field2 (CharField)>')
        self.assertEqual(Model2A.objects.count(), 4)

        oa.delete()
        objects = Model2A.objects.all()
        self.assertEqual(repr(objects[0]), '<Model2A: id 1, field1 (CharField)>')
        self.assertEqual(repr(objects[1]), '<Model2C: id 3, field1 (CharField), field2 (CharField), field3 (CharField)>')
        self.assertEqual(repr(objects[2]), '<Model2D: id 4, field1 (CharField), field2 (CharField), field3 (CharField), field4 (CharField)>')
        self.assertEqual(len(objects), 3)


    def test_combine_querysets(self):
        ModelX.objects.create(field_x='x')
        ModelY.objects.create(field_y='y')

        qs = Base.objects.instance_of(ModelX) | Base.objects.instance_of(ModelY)
        self.assertEqual(repr(qs[0]), '<ModelX: id 1, field_b (CharField), field_x (CharField)>')
        self.assertEqual(repr(qs[1]), '<ModelY: id 2, field_b (CharField), field_y (CharField)>')
        self.assertEqual(len(qs), 2)


    def test_multiple_inheritance(self):
        # multiple inheritance, subclassing third party models (mix PolymorphicModel with models.Model)

        Enhance_Base.objects.create(field_b='b-base')
        Enhance_Inherit.objects.create(field_b='b-inherit', field_p='p', field_i='i')

        qs = Enhance_Base.objects.all()
        self.assertEqual(repr(qs[0]), '<Enhance_Base: id 1, field_b (CharField) "b-base">')
        self.assertEqual(repr(qs[1]), '<Enhance_Inherit: id 2, field_b (CharField) "b-inherit", field_p (CharField) "p", field_i (CharField) "i">')
        self.assertEqual(len(qs), 2)


    def test_relation_base(self):
        # ForeignKey, ManyToManyField
        obase = RelationBase.objects.create(field_base='base')
        oa = RelationA.objects.create(field_base='A1', field_a='A2', fk=obase)
        ob = RelationB.objects.create(field_base='B1', field_b='B2', fk=oa)
        oc = RelationBC.objects.create(field_base='C1', field_b='C2', field_c='C3', fk=oa)
        oa.m2m.add(oa)
        oa.m2m.add(ob)

        objects = RelationBase.objects.all()
        self.assertEqual(repr(objects[0]), '<RelationBase: id 1, field_base (CharField) "base", fk (ForeignKey) None, m2m (ManyToManyField) 0>')
        self.assertEqual(repr(objects[1]), '<RelationA: id 2, field_base (CharField) "A1", fk (ForeignKey) RelationBase, field_a (CharField) "A2", m2m (ManyToManyField) 2>')
        self.assertEqual(repr(objects[2]), '<RelationB: id 3, field_base (CharField) "B1", fk (ForeignKey) RelationA, field_b (CharField) "B2", m2m (ManyToManyField) 1>')
        self.assertEqual(repr(objects[3]), '<RelationBC: id 4, field_base (CharField) "C1", fk (ForeignKey) RelationA, field_b (CharField) "C2", field_c (CharField) "C3", m2m (ManyToManyField) 0>')
        self.assertEqual(len(objects), 4)

        oa = RelationBase.objects.get(id=2)
        self.assertEqual(repr(oa.fk), '<RelationBase: id 1, field_base (CharField) "base", fk (ForeignKey) None, m2m (ManyToManyField) 0>')

        objects = oa.relationbase_set.all()
        self.assertEqual(repr(objects[0]), '<RelationB: id 3, field_base (CharField) "B1", fk (ForeignKey) RelationA, field_b (CharField) "B2", m2m (ManyToManyField) 1>')
        self.assertEqual(repr(objects[1]), '<RelationBC: id 4, field_base (CharField) "C1", fk (ForeignKey) RelationA, field_b (CharField) "C2", field_c (CharField) "C3", m2m (ManyToManyField) 0>')
        self.assertEqual(len(objects), 2)

        ob = RelationBase.objects.get(id=3)
        self.assertEqual(repr(ob.fk), '<RelationA: id 2, field_base (CharField) "A1", fk (ForeignKey) RelationBase, field_a (CharField) "A2", m2m (ManyToManyField) 2>')

        oa = RelationA.objects.get()
        objects = oa.m2m.all()
        self.assertEqual(repr(objects[0]), '<RelationA: id 2, field_base (CharField) "A1", fk (ForeignKey) RelationBase, field_a (CharField) "A2", m2m (ManyToManyField) 2>')
        self.assertEqual(repr(objects[1]), '<RelationB: id 3, field_base (CharField) "B1", fk (ForeignKey) RelationA, field_b (CharField) "B2", m2m (ManyToManyField) 1>')
        self.assertEqual(len(objects), 2)


    def test_user_defined_manager(self):
        self.create_model2abcd()
        ModelWithMyManager.objects.create(field1='D1a', field4='D4a')
        ModelWithMyManager.objects.create(field1='D1b', field4='D4b')

        objects = ModelWithMyManager.objects.all()   # MyManager should reverse the sorting of field1
        self.assertEqual(repr(objects[0]), '<ModelWithMyManager: id 6, field1 (CharField) "D1b", field4 (CharField) "D4b">')
        self.assertEqual(repr(objects[1]), '<ModelWithMyManager: id 5, field1 (CharField) "D1a", field4 (CharField) "D4a">')
        self.assertEqual(len(objects), 2)

        self.assertIs(type(ModelWithMyManager.objects), MyManager)
        self.assertIs(type(ModelWithMyManager._default_manager), MyManager)
        self.assertIs(type(ModelWithMyManager.base_objects), models.Manager)


    def test_manager_inheritance(self):
        # by choice of MRO, should be MyManager from MROBase1.
        self.assertIs(type(MRODerived.objects), MyManager)

        # check for correct default manager
        self.assertIs(type(MROBase1._default_manager), MyManager)

        # Django vanilla inheritance does not inherit MyManager as _default_manager here
        self.assertIs(type(MROBase2._default_manager), MyManager)


    def test_queryset_assignment(self):
        # This is just a consistency check for now, testing standard Django behavior.
        parent = PlainParentModelWithManager.objects.create()
        child = PlainChildModelWithManager.objects.create(fk=parent)
        self.assertIs(type(PlainParentModelWithManager._default_manager), models.Manager)
        self.assertIs(type(PlainChildModelWithManager._default_manager), PlainMyManager)
        self.assertIs(type(PlainChildModelWithManager.objects), PlainMyManager)
        self.assertIs(type(PlainChildModelWithManager.objects.all()), PlainMyManagerQuerySet)

        # A related set is created using the model's _default_manager, so does gain extra methods.
        self.assertIs(type(parent.childmodel_set.my_queryset_foo()), PlainMyManagerQuerySet)

        # For polymorphic models, the same should happen.
        parent = ParentModelWithManager.objects.create()
        child = ChildModelWithManager.objects.create(fk=parent)
        self.assertIs(type(ParentModelWithManager._default_manager), PolymorphicManager)
        self.assertIs(type(ChildModelWithManager._default_manager), MyManager)
        self.assertIs(type(ChildModelWithManager.objects), MyManager)
        self.assertIs(type(ChildModelWithManager.objects.my_queryset_foo()), MyManagerQuerySet)

        # A related set is created using the model's _default_manager, so does gain extra methods.
        self.assertIs(type(parent.childmodel_set.my_queryset_foo()), MyManagerQuerySet)


    def test_proxy_models(self):
        # prepare some data
        for data in ('bleep bloop', 'I am a', 'computer'):
            ProxyChild.objects.create(some_data=data)

        # this caches ContentType queries so they don't interfere with our query counts later
        list(ProxyBase.objects.all())

        # one query per concrete class
        with self.assertNumQueries(1):
            items = list(ProxyBase.objects.all())

        self.assertIsInstance(items[0], ProxyChild)


    def test_content_types_for_proxy_models(self):
        """Checks if ContentType is capable of returning proxy models."""
        from django.db.models import Model
        from django.contrib.contenttypes.models import ContentType

        ct = ContentType.objects.get_for_model(ProxyChild, for_concrete_model=False)
        self.assertEqual(ProxyChild, ct.model_class())


    def test_proxy_model_inheritance(self):
        """
        Polymorphic abilities should also work when the base model is a proxy object.
        """
        # The managers should point to the proper objects.
        # otherwise, the whole excersise is pointless.
        self.assertEqual(ProxiedBase.objects.model, ProxiedBase)
        self.assertEqual(ProxyModelBase.objects.model, ProxyModelBase)
        self.assertEqual(ProxyModelA.objects.model, ProxyModelA)
        self.assertEqual(ProxyModelB.objects.model, ProxyModelB)

        # Create objects
        ProxyModelA.objects.create(name="object1")
        ProxyModelB.objects.create(name="object2", field2="bb")

        # Getting single objects
        object1 = ProxyModelBase.objects.get(name='object1')
        object2 = ProxyModelBase.objects.get(name='object2')
        self.assertEqual(repr(object1), '<ProxyModelA: id 1, name (CharField) "object1", field1 (CharField) "">')
        self.assertEqual(repr(object2), '<ProxyModelB: id 2, name (CharField) "object2", field2 (CharField) "bb">')
        self.assertIsInstance(object1, ProxyModelA)
        self.assertIsInstance(object2, ProxyModelB)

        # Same for lists
        objects = list(ProxyModelBase.objects.all().order_by('name'))
        self.assertEqual(repr(objects[0]), '<ProxyModelA: id 1, name (CharField) "object1", field1 (CharField) "">')
        self.assertEqual(repr(objects[1]), '<ProxyModelB: id 2, name (CharField) "object2", field2 (CharField) "bb">')
        self.assertIsInstance(objects[0], ProxyModelA)
        self.assertIsInstance(objects[1], ProxyModelB)


    def test_fix_getattribute(self):
        ### fixed issue in PolymorphicModel.__getattribute__: field name same as model name
        o = ModelFieldNameTest.objects.create(modelfieldnametest='1')
        self.assertEqual(repr(o), '<ModelFieldNameTest: id 1, modelfieldnametest (CharField)>')

        # if subclass defined __init__ and accessed class members,
        # __getattribute__ had a problem: "...has no attribute 'sub_and_superclass_dict'"
        o = InitTestModelSubclass.objects.create()
        self.assertEqual(o.bar, 'XYZ')


class RegressionTests(TestCase):

    def test_for_query_result_incomplete_with_inheritance(self):
        """ https://github.com/bconstantin/django_polymorphic/issues/15 """

        top = Top()
        top.save()
        middle = Middle()
        middle.save()
        bottom = Bottom()
        bottom.save()

        expected_queryset = [top, middle, bottom]
        self.assertQuerysetEqual(Top.objects.all(), [repr(r) for r in expected_queryset])

        expected_queryset = [middle, bottom]
        self.assertQuerysetEqual(Middle.objects.all(), [repr(r) for r in expected_queryset])

        expected_queryset = [bottom]
        self.assertQuerysetEqual(Bottom.objects.all(), [repr(r) for r in expected_queryset])


# -*- coding: utf-8 -*-
"""
Seamless Polymorphic Inheritance for Django Models
==================================================

Please see README.rst and DOCS.rst for further information.

Or on the Web:
http://chrisglass.github.com/django_polymorphic/
http://github.com/chrisglass/django_polymorphic

Copyright:
This code and affiliated files are (C) by Bert Constantin and individual contributors.
Please see LICENSE and AUTHORS for more information.
"""
from __future__ import absolute_import

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.utils import six

from .base import PolymorphicModelBase
from .manager import PolymorphicManager
from .query_translate import translate_polymorphic_Q_object


###################################################################################
### PolymorphicModel

class PolymorphicModel(six.with_metaclass(PolymorphicModelBase, models.Model)):
    """
    Abstract base class that provides polymorphic behaviour
    for any model directly or indirectly derived from it.

    For usage instructions & examples please see documentation.

    PolymorphicModel declares one field for internal use (polymorphic_ctype)
    and provides a polymorphic manager as the default manager
    (and as 'objects').

    PolymorphicModel overrides the save() and __init__ methods.

    If your derived class overrides any of these methods as well, then you need
    to take care that you correctly call the method of the superclass, like:

        super(YourClass,self).save(*args,**kwargs)
    """

    # for PolymorphicModelBase, so it can tell which models are polymorphic and which are not (duck typing)
    polymorphic_model_marker = True

    # for PolymorphicQuery, True => an overloaded __repr__ with nicer multi-line output is used by PolymorphicQuery
    polymorphic_query_multiline_output = False

    class Meta:
        abstract = True

    # avoid ContentType related field accessor clash (an error emitted by model validation)
    polymorphic_ctype = models.ForeignKey(ContentType, null=True, editable=False,
                                related_name='polymorphic_%(app_label)s.%(class)s_set')

    # some applications want to know the name of the fields that are added to its models
    polymorphic_internal_model_fields = ['polymorphic_ctype']

    # Note that Django 1.5 removes these managers because the model is abstract.
    # They are pretended to be there by the metaclass in PolymorphicModelBase.get_inherited_managers()
    objects = PolymorphicManager()
    base_objects = models.Manager()

    @classmethod
    def translate_polymorphic_Q_object(self_class, q):
        return translate_polymorphic_Q_object(self_class, q)

    def pre_save_polymorphic(self):
        """Normally not needed.
        This function may be called manually in special use-cases. When the object
        is saved for the first time, we store its real class in polymorphic_ctype.
        When the object later is retrieved by PolymorphicQuerySet, it uses this
        field to figure out the real class of this object
        (used by PolymorphicQuerySet._get_real_instances)
        """
        if not self.polymorphic_ctype_id:
            self.polymorphic_ctype = ContentType.objects.get_for_model(self, for_concrete_model=False)

    def save(self, *args, **kwargs):
        """Overridden model save function which supports the polymorphism
        functionality (through pre_save_polymorphic)."""
        self.pre_save_polymorphic()
        return super(PolymorphicModel, self).save(*args, **kwargs)

    def get_real_instance_class(self):
        """
        Normally not needed.
        If a non-polymorphic manager (like base_objects) has been used to
        retrieve objects, then the real class/type of these objects may be
        determined using this method.
        """
        # the following line would be the easiest way to do this, but it produces sql queries
        # return self.polymorphic_ctype.model_class()
        # so we use the following version, which uses the CopntentType manager cache.
        # Note that model_class() can return None for stale content types;
        # when the content type record still exists but no longer refers to an existing model.
        try:
            return ContentType.objects.get_for_id(self.polymorphic_ctype_id).model_class()
        except AttributeError:
            # Django <1.6 workaround
            return None

    def get_real_concrete_instance_class_id(self):
        model_class = self.get_real_instance_class()
        if model_class is None:
            return None
        return ContentType.objects.get_for_model(model_class, for_concrete_model=True).pk

    def get_real_concrete_instance_class(self):
        model_class = self.get_real_instance_class()
        if model_class is None:
            return None
        return ContentType.objects.get_for_model(model_class, for_concrete_model=True).model_class()

    def get_real_instance(self):
        """Normally not needed.
        If a non-polymorphic manager (like base_objects) has been used to
        retrieve objects, then the complete object with it's real class/type
        and all fields may be retrieved with this method.
        Each method call executes one db query (if necessary)."""
        real_model = self.get_real_instance_class()
        if real_model == self.__class__:
            return self
        return real_model.objects.get(pk=self.pk)

    def __init__(self, * args, ** kwargs):
        """Replace Django's inheritance accessor member functions for our model
        (self.__class__) with our own versions.
        We monkey patch them until a patch can be added to Django
        (which would probably be very small and make all of this obsolete).

        If we have inheritance of the form ModelA -> ModelB ->ModelC then
        Django creates accessors like this:
        - ModelA: modelb
        - ModelB: modela_ptr, modelb, modelc
        - ModelC: modela_ptr, modelb, modelb_ptr, modelc

        These accessors allow Django (and everyone else) to travel up and down
        the inheritance tree for the db object at hand.

        The original Django accessors use our polymorphic manager.
        But they should not. So we replace them with our own accessors that use
        our appropriate base_objects manager.
        """
        super(PolymorphicModel, self).__init__(*args, ** kwargs)

        if self.__class__.polymorphic_super_sub_accessors_replaced:
            return
        self.__class__.polymorphic_super_sub_accessors_replaced = True

        def create_accessor_function_for_model(model, accessor_name):
            def accessor_function(self):
                attr = model.base_objects.get(pk=self.pk)
                return attr
            return accessor_function

        subclasses_and_superclasses_accessors = self._get_inheritance_relation_fields_and_models()

        from django.db.models.fields.related import SingleRelatedObjectDescriptor, ReverseSingleRelatedObjectDescriptor
        for name, model in subclasses_and_superclasses_accessors.items():
            orig_accessor = getattr(self.__class__, name, None)
            if type(orig_accessor) in [SingleRelatedObjectDescriptor, ReverseSingleRelatedObjectDescriptor]:
                #print >>sys.stderr, '---------- replacing', name, orig_accessor, '->', model
                setattr(self.__class__, name, property(create_accessor_function_for_model(model, name)))

    def _get_inheritance_relation_fields_and_models(self):
        """helper function for __init__:
        determine names of all Django inheritance accessor member functions for type(self)"""

        def add_model(model, as_ptr, result):
            name = model.__name__.lower()
            if as_ptr:
                name += '_ptr'
            result[name] = model

        def add_model_if_regular(model, as_ptr, result):
            if (issubclass(model, models.Model)
                and model != models.Model
                and model != self.__class__
                and model != PolymorphicModel):
                add_model(model, as_ptr, result)

        def add_all_super_models(model, result):
            add_model_if_regular(model, True, result)
            for b in model.__bases__:
                add_all_super_models(b, result)

        def add_all_sub_models(model, result):
            for b in model.__subclasses__():
                add_model_if_regular(b, False, result)

        result = {}
        add_all_super_models(self.__class__, result)
        add_all_sub_models(self.__class__, result)
        return result

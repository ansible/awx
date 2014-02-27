# -*- coding: utf-8 -*-
""" QuerySet for PolymorphicModel
    Please see README.rst or DOCS.rst or http://chrisglass.github.com/django_polymorphic/
"""
from __future__ import absolute_import

from collections import defaultdict

from django.db.models.query import QuerySet
from django.contrib.contenttypes.models import ContentType
from django.utils import six

from .query_translate import translate_polymorphic_filter_definitions_in_kwargs, translate_polymorphic_filter_definitions_in_args
from .query_translate import translate_polymorphic_field_path

# chunk-size: maximum number of objects requested per db-request
# by the polymorphic queryset.iterator() implementation; we use the same chunk size as Django
try:
    from django.db.models.query import CHUNK_SIZE               # this is 100 for Django 1.1/1.2
except ImportError:
    # CHUNK_SIZE was removed in Django 1.6
    CHUNK_SIZE = 100
Polymorphic_QuerySet_objects_per_request = CHUNK_SIZE


def transmogrify(cls, obj):
    """
    Upcast a class to a different type without asking questions.
    """
    if not '__init__' in obj.__dict__:
        # Just assign __class__ to a different value.
        new = obj
        new.__class__ = cls
    else:
        # Run constructor, reassign values
        new = cls()
        for k,v in obj.__dict__.items():
            new.__dict__[k] = v
    return new


###################################################################################
### PolymorphicQuerySet

class PolymorphicQuerySet(QuerySet):
    """
    QuerySet for PolymorphicModel

    Contains the core functionality for PolymorphicModel

    Usually not explicitly needed, except if a custom queryset class
    is to be used.
    """

    def __init__(self, *args, **kwargs):
        "init our queryset object member variables"
        self.polymorphic_disabled = False
        super(PolymorphicQuerySet, self).__init__(*args, **kwargs)

    def _clone(self, *args, **kwargs):
        "Django's _clone only copies its own variables, so we need to copy ours here"
        new = super(PolymorphicQuerySet, self)._clone(*args, **kwargs)
        new.polymorphic_disabled = self.polymorphic_disabled
        return new

    def non_polymorphic(self, *args, **kwargs):
        """switch off polymorphic behaviour for this query.
        When the queryset is evaluated, only objects of the type of the
        base class used for this query are returned."""
        self.polymorphic_disabled = True
        return self

    def instance_of(self, *args):
        """Filter the queryset to only include the classes in args (and their subclasses).
        Implementation in _translate_polymorphic_filter_defnition."""
        return self.filter(instance_of=args)

    def not_instance_of(self, *args):
        """Filter the queryset to exclude the classes in args (and their subclasses).
        Implementation in _translate_polymorphic_filter_defnition."""
        return self.filter(not_instance_of=args)

    def _filter_or_exclude(self, negate, *args, **kwargs):
        "We override this internal Django functon as it is used for all filter member functions."
        translate_polymorphic_filter_definitions_in_args(self.model, args)  # the Q objects
        additional_args = translate_polymorphic_filter_definitions_in_kwargs(self.model, kwargs)  # filter_field='data'
        return super(PolymorphicQuerySet, self)._filter_or_exclude(negate, *(list(args) + additional_args), **kwargs)

    def order_by(self, *args, **kwargs):
        """translate the field paths in the args, then call vanilla order_by."""
        new_args = [translate_polymorphic_field_path(self.model, a) for a in args]
        return super(PolymorphicQuerySet, self).order_by(*new_args, **kwargs)

    def _process_aggregate_args(self, args, kwargs):
        """for aggregate and annotate kwargs: allow ModelX___field syntax for kwargs, forbid it for args.
        Modifies kwargs if needed (these are Aggregate objects, we translate the lookup member variable)"""
        for a in args:
            assert not '___' in a.lookup, 'PolymorphicModel: annotate()/aggregate(): ___ model lookup supported for keyword arguments only'
        for a in six.itervalues(kwargs):
            a.lookup = translate_polymorphic_field_path(self.model, a.lookup)

    def annotate(self, *args, **kwargs):
        """translate the polymorphic field paths in the kwargs, then call vanilla annotate.
        _get_real_instances will do the rest of the job after executing the query."""
        self._process_aggregate_args(args, kwargs)
        return super(PolymorphicQuerySet, self).annotate(*args, **kwargs)

    def aggregate(self, *args, **kwargs):
        """translate the polymorphic field paths in the kwargs, then call vanilla aggregate.
        We need no polymorphic object retrieval for aggregate => switch it off."""
        self._process_aggregate_args(args, kwargs)
        self.polymorphic_disabled = True
        return super(PolymorphicQuerySet, self).aggregate(*args, **kwargs)

    # Since django_polymorphic 'V1.0 beta2', extra() always returns polymorphic results.^
    # The resulting objects are required to have a unique primary key within the result set
    # (otherwise an error is thrown).
    # The "polymorphic" keyword argument is not supported anymore.
    #def extra(self, *args, **kwargs):

    def _get_real_instances(self, base_result_objects):
        """
        Polymorphic object loader

        Does the same as:

            return [ o.get_real_instance() for o in base_result_objects ]

        but more efficiently.

        The list base_result_objects contains the objects from the executed
        base class query. The class of all of them is self.model (our base model).

        Some, many or all of these objects were not created and stored as
        class self.model, but as a class derived from self.model. We want to re-fetch
        these objects from the db as their original class so we can return them
        just as they were created/saved.

        We identify these objects by looking at o.polymorphic_ctype, which specifies
        the real class of these objects (the class at the time they were saved).

        First, we sort the result objects in base_result_objects for their
        subclass (from o.polymorphic_ctype), and then we execute one db query per
        subclass of objects. Here, we handle any annotations from annotate().

        Finally we re-sort the resulting objects into the correct order and
        return them as a list.
        """
        ordered_id_list = []    # list of ids of result-objects in correct order
        results = {}            # polymorphic dict of result-objects, keyed with their id (no order)

        # dict contains one entry per unique model type occurring in result,
        # in the format idlist_per_model[modelclass]=[list-of-object-ids]
        idlist_per_model = defaultdict(list)

        # - sort base_result_object ids into idlist_per_model lists, depending on their real class;
        # - also record the correct result order in "ordered_id_list"
        # - store objects that already have the correct class into "results"
        base_result_objects_by_id = {}
        self_model_class_id = ContentType.objects.get_for_model(self.model, for_concrete_model=False).pk
        self_concrete_model_class_id = ContentType.objects.get_for_model(self.model, for_concrete_model=True).pk

        for base_object in base_result_objects:
            ordered_id_list.append(base_object.pk)

            # check if id of the result object occeres more than once - this can happen e.g. with base_objects.extra(tables=...)
            if not base_object.pk in base_result_objects_by_id:
                base_result_objects_by_id[base_object.pk] = base_object

                if base_object.polymorphic_ctype_id == self_model_class_id:
                    # Real class is exactly the same as base class, go straight to results
                    results[base_object.pk] = base_object

                else:
                    real_concrete_class = base_object.get_real_instance_class()
                    real_concrete_class_id = base_object.get_real_concrete_instance_class_id()

                    if real_concrete_class_id is None:
                        # Dealing with a stale content type
                        continue
                    elif real_concrete_class_id == self_concrete_model_class_id:
                        # Real and base classes share the same concrete ancestor,
                        # upcast it and put it in the results
                        results[base_object.pk] = transmogrify(real_concrete_class, base_object)
                    else:
                        real_concrete_class = ContentType.objects.get_for_id(real_concrete_class_id).model_class()
                        idlist_per_model[real_concrete_class].append(base_object.pk)

        # django's automatic ".pk" field does not always work correctly for
        # custom fields in derived objects (unclear yet who to put the blame on).
        # We get different type(o.pk) in this case.
        # We work around this by using the real name of the field directly
        # for accessing the primary key of the the derived objects.
        # We might assume that self.model._meta.pk.name gives us the name of the primary key field,
        # but it doesn't. Therefore we use polymorphic_primary_key_name, which we set up in base.py.
        pk_name = self.model.polymorphic_primary_key_name

        # For each model in "idlist_per_model" request its objects (the real model)
        # from the db and store them in results[].
        # Then we copy the annotate fields from the base objects to the real objects.
        # Then we copy the extra() select fields from the base objects to the real objects.
        # TODO: defer(), only(): support for these would be around here
        for real_concrete_class, idlist in idlist_per_model.items():
            real_objects = real_concrete_class.base_objects.filter(pk__in=idlist)  # use pk__in instead ####
            real_objects.query.select_related = self.query.select_related  # copy select related configuration to new qs

            for real_object in real_objects:
                o_pk = getattr(real_object, pk_name)
                real_class = real_object.get_real_instance_class()

                # If the real class is a proxy, upcast it
                if real_class != real_concrete_class:
                    real_object = transmogrify(real_class, real_object)

                if self.query.aggregates:
                    for anno_field_name in six.iterkeys(self.query.aggregates):
                        attr = getattr(base_result_objects_by_id[o_pk], anno_field_name)
                        setattr(real_object, anno_field_name, attr)

                if self.query.extra_select:
                    for select_field_name in six.iterkeys(self.query.extra_select):
                        attr = getattr(base_result_objects_by_id[o_pk], select_field_name)
                        setattr(real_object, select_field_name, attr)

                results[o_pk] = real_object

        # re-create correct order and return result list
        resultlist = [results[ordered_id] for ordered_id in ordered_id_list if ordered_id in results]

        # set polymorphic_annotate_names in all objects (currently just used for debugging/printing)
        if self.query.aggregates:
            annotate_names = six.iterkeys(self.query.aggregates)  # get annotate field list
            for real_object in resultlist:
                real_object.polymorphic_annotate_names = annotate_names

        # set polymorphic_extra_select_names in all objects (currently just used for debugging/printing)
        if self.query.extra_select:
            extra_select_names = six.iterkeys(self.query.extra_select)  # get extra select field list
            for real_object in resultlist:
                real_object.polymorphic_extra_select_names = extra_select_names

        return resultlist

    def iterator(self):
        """
        This function is used by Django for all object retrieval.
        By overriding it, we modify the objects that this queryset returns
        when it is evaluated (or its get method or other object-returning methods are called).

        Here we do the same as:

            base_result_objects=list(super(PolymorphicQuerySet, self).iterator())
            real_results=self._get_real_instances(base_result_objects)
            for o in real_results: yield o

        but it requests the objects in chunks from the database,
        with Polymorphic_QuerySet_objects_per_request per chunk
        """
        base_iter = super(PolymorphicQuerySet, self).iterator()

        # disabled => work just like a normal queryset
        if self.polymorphic_disabled:
            for o in base_iter:
                yield o
            raise StopIteration

        while True:
            base_result_objects = []
            reached_end = False

            for i in range(Polymorphic_QuerySet_objects_per_request):
                try:
                    o = next(base_iter)
                    base_result_objects.append(o)
                except StopIteration:
                    reached_end = True
                    break

            real_results = self._get_real_instances(base_result_objects)

            for o in real_results:
                yield o

            if reached_end:
                raise StopIteration

    def __repr__(self, *args, **kwargs):
        if self.model.polymorphic_query_multiline_output:
            result = [repr(o) for o in self.all()]
            return  '[ ' + ',\n  '.join(result) + ' ]'
        else:
            return super(PolymorphicQuerySet, self).__repr__(*args, **kwargs)

    class _p_list_class(list):
        def __repr__(self, *args, **kwargs):
            result = [repr(o) for o in self]
            return  '[ ' + ',\n  '.join(result) + ' ]'

    def get_real_instances(self, base_result_objects=None):
        "same as _get_real_instances, but make sure that __repr__ for ShowField... creates correct output"
        if not base_result_objects:
            base_result_objects = self
        olist = self._get_real_instances(base_result_objects)
        if not self.model.polymorphic_query_multiline_output:
            return olist
        clist = PolymorphicQuerySet._p_list_class(olist)
        return clist

from django.contrib.contenttypes.models import ContentType
from django.db.models.deletion import (
    DO_NOTHING, Collector, get_candidate_relations_to_delete,
)
from collections import Counter, OrderedDict
from django.db import transaction
from django.db.models import sql


def bulk_related_objects(field, objs, using):
    # This overrides the method in django.contrib.contenttypes.fields.py
    """
    Return all objects related to ``objs`` via this ``GenericRelation``.
    """
    return field.remote_field.model._base_manager.db_manager(using).filter(**{
        "%s__pk" % field.content_type_field_name: ContentType.objects.db_manager(using).get_for_model(
            field.model, for_concrete_model=field.for_concrete_model).pk,
        "%s__in" % field.object_id_field_name: list(objs.values_list('pk', flat=True))
    })


def pre_delete(qs):
    # taken from .delete method in django.db.models.query.py
    assert qs.query.can_filter(), \
        "Cannot use 'limit' or 'offset' with delete."

    if qs._fields is not None:
        raise TypeError("Cannot call delete() after .values() or .values_list()")

    del_query = qs._chain()

    # The delete is actually 2 queries - one to find related objects,
    # and one to delete. Make sure that the discovery of related
    # objects is performed on the same database as the deletion.
    del_query._for_write = True

    # Disable non-supported fields.
    del_query.query.select_for_update = False
    del_query.query.select_related = False
    del_query.query.clear_ordering(force_empty=True)
    return del_query


class AWXCollector(Collector):

    def add(self, objs, source=None, nullable=False, reverse_dependency=False):
        """
        Add 'objs' to the collection of objects to be deleted.  If the call is
        the result of a cascade, 'source' should be the model that caused it,
        and 'nullable' should be set to True if the relation can be null.

        Return a list of all objects that were not already collected.
        """
        if not objs.exists():
            return objs
        model = objs.model
        self.data.setdefault(model, [])
        self.data[model].append(objs)
        # Nullable relationships can be ignored -- they are nulled out before
        # deleting, and therefore do not affect the order in which objects have
        # to be deleted.
        if source is not None and not nullable:
            if reverse_dependency:
                source, model = model, source
            self.dependencies.setdefault(
                source._meta.concrete_model, set()).add(model._meta.concrete_model)
        return objs

    def add_field_update(self, field, value, objs):
        """
        Schedule a field update. 'objs' must be a homogeneous iterable
        collection of model instances (e.g. a QuerySet).
        """
        if not objs.exists():
            return
        model = objs.model
        self.field_updates.setdefault(model, {})
        self.field_updates[model].setdefault((field, value), [])
        self.field_updates[model][(field, value)].append(objs)

    def collect(self, objs, source=None, nullable=False, collect_related=True,
                source_attr=None, reverse_dependency=False, keep_parents=False):
        """
        Add 'objs' to the collection of objects to be deleted as well as all
        parent instances.  'objs' must be a homogeneous iterable collection of
        model instances (e.g. a QuerySet).  If 'collect_related' is True,
        related objects will be handled by their respective on_delete handler.

        If the call is the result of a cascade, 'source' should be the model
        that caused it and 'nullable' should be set to True, if the relation
        can be null.

        If 'reverse_dependency' is True, 'source' will be deleted before the
        current model, rather than after. (Needed for cascading to parent
        models, the one case in which the cascade follows the forwards
        direction of an FK rather than the reverse direction.)

        If 'keep_parents' is True, data of parent model's will be not deleted.
        """

        if hasattr(objs, 'polymorphic_disabled'):
            objs.polymorphic_disabled = True

        if self.can_fast_delete(objs):
            self.fast_deletes.append(objs)
            return
        new_objs = self.add(objs, source, nullable,
                            reverse_dependency=reverse_dependency)
        if not new_objs.exists():
            return

        model = new_objs.model

        if not keep_parents:
            # Recursively collect concrete model's parent models, but not their
            # related objects. These will be found by meta.get_fields()
            concrete_model = model._meta.concrete_model
            for ptr in concrete_model._meta.parents.keys():
                if ptr:
                    parent_objs = ptr.objects.filter(pk__in = new_objs.values_list('pk', flat=True))
                    self.collect(parent_objs, source=model,
                                 collect_related=False,
                                 reverse_dependency=True)
        if collect_related:
            parents = model._meta.parents
            for related in get_candidate_relations_to_delete(model._meta):
                # Preserve parent reverse relationships if keep_parents=True.
                if keep_parents and related.model in parents:
                    continue
                field = related.field
                if field.remote_field.on_delete == DO_NOTHING:
                    continue
                related_qs = self.related_objects(related, new_objs)
                if self.can_fast_delete(related_qs, from_field=field):
                    self.fast_deletes.append(related_qs)
                elif related_qs:
                    field.remote_field.on_delete(self, field, related_qs, self.using)
            for field in model._meta.private_fields:
                if hasattr(field, 'bulk_related_objects'):
                    # It's something like generic foreign key.
                    sub_objs = bulk_related_objects(field, new_objs, self.using)
                    self.collect(sub_objs, source=model, nullable=True)

    def delete(self):
        self.sort()

        # collect pk_list before deletion (once things start to delete
        # queries might not be able to retreive pk list)
        del_dict = OrderedDict()
        for model, instances in self.data.items():
            del_dict.setdefault(model, [])
            for inst in instances:
                del_dict[model] += list(inst.values_list('pk', flat=True))

        deleted_counter = Counter()

        with transaction.atomic(using=self.using, savepoint=False):

            # update fields
            for model, instances_for_fieldvalues in self.field_updates.items():
                for (field, value), instances in instances_for_fieldvalues.items():
                    for inst in instances:
                        query = sql.UpdateQuery(model)
                        query.update_batch(inst.values_list('pk', flat=True),
                                           {field.name: value}, self.using)
            # fast deletes
            for qs in self.fast_deletes:
                count = qs._raw_delete(using=self.using)
                deleted_counter[qs.model._meta.label] += count

            # delete instances
            for model, pk_list in del_dict.items():
                query = sql.DeleteQuery(model)
                count = query.delete_batch(pk_list, self.using)
                deleted_counter[model._meta.label] += count

            return sum(deleted_counter.values()), dict(deleted_counter)

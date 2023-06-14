# Django
from django.db import models
from django.db.models.signals import m2m_changed
from django.db.models.fields.related_descriptors import (
    ManyToManyDescriptor,
    create_forward_many_to_many_manager,
)
from django.utils.functional import cached_property


class OrderedManyToManyDescriptor(ManyToManyDescriptor):
    """
    Django doesn't seem to support:

    class Meta:
        ordering = [...]

    ...on custom through= relations for ManyToMany fields.

    Meaning, queries made _through_ the intermediary table will _not_ apply an
    ORDER_BY clause based on the `Meta.ordering` of the intermediary M2M class
    (which is the behavior we want for "ordered" many to many relations):

    https://github.com/django/django/blob/stable/1.11.x/django/db/models/fields/related_descriptors.py#L593

    This descriptor automatically sorts all queries through this relation
    using the `position` column on the M2M table.
    """

    @cached_property
    def related_manager_cls(self):
        model = self.rel.related_model if self.reverse else self.rel.model

        def add_custom_queryset_to_many_related_manager(many_related_manage_cls):
            class OrderedManyRelatedManager(many_related_manage_cls):
                def get_queryset(self):
                    return super(OrderedManyRelatedManager, self).get_queryset().order_by('%s__position' % self.through._meta.model_name)

                def add(self, *objects):
                    if len(objects) > 1:
                        raise RuntimeError('Ordered many-to-many fields do not support multiple objects')
                    return super().add(*objects)

                def remove(self, *objects):
                    if len(objects) > 1:
                        raise RuntimeError('Ordered many-to-many fields do not support multiple objects')
                    return super().remove(*objects)

            return OrderedManyRelatedManager

        return add_custom_queryset_to_many_related_manager(
            create_forward_many_to_many_manager(
                model._default_manager.__class__,
                self.rel,
                reverse=self.reverse,
            )
        )


class OrderedManyToManyField(models.ManyToManyField):
    """
    A ManyToManyField that automatically sorts all querysets
    by a special `position` column on the M2M table
    """

    def _update_m2m_position(self, sender, instance, action, **kwargs):
        if action in ('post_add', 'post_remove'):
            descriptor = getattr(instance, self.name)
            order_with_respect_to = descriptor.source_field_name

            for i, ig in enumerate(sender.objects.filter(**{order_with_respect_to: instance.pk})):
                if ig.position != i:
                    ig.position = i
                    ig.save()

    def contribute_to_class(self, cls, name, **kwargs):
        super(OrderedManyToManyField, self).contribute_to_class(cls, name, **kwargs)
        setattr(cls, name, OrderedManyToManyDescriptor(self.remote_field, reverse=False))

        through = getattr(cls, name).through
        if isinstance(through, str) and "." not in through:
            # support lazy loading of string model names
            through = '.'.join([cls._meta.app_label, through])
        m2m_changed.connect(self._update_m2m_position, sender=through)

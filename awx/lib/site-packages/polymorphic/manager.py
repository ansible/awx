# -*- coding: utf-8 -*-
""" PolymorphicManager
    Please see README.rst or DOCS.rst or http://chrisglass.github.com/django_polymorphic/
"""
from __future__ import unicode_literals
import warnings
from django.db import models
from polymorphic.query import PolymorphicQuerySet


class PolymorphicManager(models.Manager):
    """
    Manager for PolymorphicModel

    Usually not explicitly needed, except if a custom manager or
    a custom queryset class is to be used.
    """
    # Tell Django that related fields also need to use this manager:
    use_for_related_fields = True
    queryset_class = PolymorphicQuerySet

    def __init__(self, queryset_class=None, *args, **kwrags):
        # Up till polymorphic 0.4, the queryset class could be specified as parameter to __init__.
        # However, this doesn't work for related managers which instantiate a new version of this class.
        # Hence, for custom managers the new default is using the 'queryset_class' attribute at class level instead.
        if queryset_class:
            warnings.warn("Using PolymorphicManager(queryset_class=..) is deprecated; override the queryset_class attribute instead", DeprecationWarning)
            # For backwards compatibility, still allow the parameter:
            self.queryset_class = queryset_class

        super(PolymorphicManager, self).__init__(*args, **kwrags)

    def get_query_set(self):
        return self.queryset_class(self.model, using=self._db)

    # Proxy all unknown method calls to the queryset, so that its members are
    # directly accessible as PolymorphicModel.objects.*
    # The advantage of this method is that not yet known member functions of derived querysets will be proxied as well.
    # We exclude any special functions (__) from this automatic proxying.
    def __getattr__(self, name):
        if name.startswith('__'):
            return super(PolymorphicManager, self).__getattr__(self, name)
        return getattr(self.get_query_set(), name)

    def __unicode__(self):
        return '%s (PolymorphicManager) using %s' % (self.__class__.__name__, self.queryset_class.__name__)

# -*- coding: utf-8 -*-
"""
Seamless Polymorphic Inheritance for Django Models

Copyright:
This code and affiliated files are (C) by Bert Constantin and individual contributors.
Please see LICENSE and AUTHORS for more information.
"""
from __future__ import absolute_import
import django
from .polymorphic_model import PolymorphicModel
from .manager import PolymorphicManager
from .query import PolymorphicQuerySet
from .query_translate import translate_polymorphic_Q_object
from .showfields import ShowFieldContent, ShowFieldType, ShowFieldTypeAndContent
from .showfields import ShowFields, ShowFieldTypes, ShowFieldsAndTypes  # import old names for compatibility


# Monkey-patch Django < 1.5 to allow ContentTypes for proxy models.
if django.VERSION[:2] < (1, 5):
    from django.contrib.contenttypes.models import ContentTypeManager
    from django.utils.encoding import smart_text

    def get_for_model(self, model, for_concrete_model=True):
        if for_concrete_model:
            model = model._meta.concrete_model
        elif model._deferred:
            model = model._meta.proxy_for_model

        opts = model._meta

        try:
            ct = self._get_from_cache(opts)
        except KeyError:
            ct, created = self.get_or_create(
                app_label = opts.app_label,
                model = opts.object_name.lower(),
                defaults = {'name': smart_text(opts.verbose_name_raw)},
            )
            self._add_to_cache(self.db, ct)

        return ct

    ContentTypeManager.get_for_model__original = ContentTypeManager.get_for_model
    ContentTypeManager.get_for_model = get_for_model


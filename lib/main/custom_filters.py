# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved

from rest_framework.filters import BaseFilterBackend
from django.core.exceptions import PermissionDenied

# TODO: does order_by still work?

class CustomFilterBackend(object):

    def filter_queryset(self, request, queryset, view):

        terms = {}
        order_by = None

        # Filtering by is_active/active that was previously in BaseList.
        qs = queryset
        for field in queryset.model._meta.fields:
            if field.name == 'is_active':
                qs = qs.filter(is_active=True)
            elif field.name == 'active':
                qs = qs.filter(active=True)

        for key, value in request.QUERY_PARAMS.items():

            if key in [ 'page', 'page_size', 'format' ]:
               continue

            if key in ('order', 'order_by'):
               order_by = value
               continue

            key2 = key
            if key2.endswith("__int"):
               key2 = key.replace("__int","")
               value = int(value)

            terms[key2] = value

        qs = qs.filter(**terms)

        if order_by:
           qs = qs.order_by(order_by)

        return qs

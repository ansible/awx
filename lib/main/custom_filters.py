# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved

from rest_framework.filters import BaseFilterBackend
from django.core.exceptions import PermissionDenied

# TODO: does order_by still work?

class CustomFilterBackend(object):

    def filter_queryset(self, request, queryset, view):

        terms = {}
        order_by = None

        for key, value in request.GET.items():

            if key in [ 'page', 'page_size', 'format' ]:
               continue

            if key == 'order_by':
               order_by = value
               continue

            key2 = key
            if key2.endswith("__int"):
               key2 = key.replace("__int","")
               value = int(value)

            terms[key2] = value

        qs = queryset.filter(**terms)

        if order_by:
           qs = qs.order_by(order_by)

        return qs

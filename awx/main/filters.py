# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

# Django
from django.core.exceptions import FieldError

# Django REST Framework
from rest_framework.exceptions import ParseError
from rest_framework.filters import BaseFilterBackend

class DefaultFilterBackend(BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):

        # Filtering by is_active/active that was previously in BaseList.
        qs = queryset
        for field in queryset.model._meta.fields:
            if field.name == 'is_active':
                qs = qs.filter(is_active=True)
            elif field.name == 'active':
                qs = qs.filter(active=True)

        # Apply filters and ordering specified via QUERY_PARAMS.
        try:

            filters = {}
            order_by = None

            for key, value in request.QUERY_PARAMS.items():

                if key in ('page', 'page_size', 'format'):
                    continue

                if key in ('order', 'order_by'):
                    order_by = value
                    continue

                if key.endswith('__int'):
                    key = key.replace('__int', '')
                    value = int(value)

                filters[key] = value

            qs = qs.filter(**filters)

            if order_by:
                qs = qs.order_by(order_by)

        except (FieldError, ValueError), e:
            # Handle invalid field names or values and return a 400.
            raise ParseError(*e.args)

        return qs

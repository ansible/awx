# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

# Django REST Framework
from rest_framework import serializers, pagination
from rest_framework.templatetags.rest_framework import replace_query_param

class NextPageField(pagination.NextPageField):
    '''Pagination field to output URL path.'''

    def to_native(self, value):
        if not value.has_next():
            return None
        page = value.next_page_number()
        request = self.context.get('request')
        url = request and request.get_full_path() or ''
        return replace_query_param(url, self.page_field, page)

class PreviousPageField(pagination.NextPageField):
    '''Pagination field to output URL path.'''

    def to_native(self, value):
        if not value.has_previous():
            return None
        page = value.previous_page_number()
        request = self.context.get('request')
        url = request and request.get_full_path() or ''
        return replace_query_param(url, self.page_field, page)

class PaginationSerializer(pagination.BasePaginationSerializer):
    '''
    Custom pagination serializer to output only URL path (without host/port).
    '''

    count = serializers.Field(source='paginator.count')
    next = NextPageField(source='*')
    previous = PreviousPageField(source='*')

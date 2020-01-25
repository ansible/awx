# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Django REST Framework
import collections
from django.conf import settings
from django.core.paginator import Paginator as DjangoPaginator
from django.template import loader
from rest_framework import pagination
from rest_framework.response import Response
from rest_framework.utils.urls import replace_query_param


class DisabledPaginator(DjangoPaginator):

    @property
    def num_pages(self):
        return 1

    @property
    def count(self):
        return 200


class LargeScalePagination(pagination.PageNumberPagination):

    page_size_query_param = 'page_size'
    max_page_size = settings.MAX_PAGE_SIZE

    def paginate_queryset(self, queryset, request, view=None):
        page_size = self.get_page_size(request)
        if not page_size:
            return None
        self.order_by = request.query_params.get('order_by') or 'id'
        after = request.query_params.get('after')
        operation = 'gt'
        if self.order_by.startswith('-'):
            self.order_by = self.order_by[1:]
            operation = 'lt'
        if after:
            queryset = queryset.filter(**{f'{self.order_by}__{operation}': after})
        self.request = request
        results = list(queryset[:(page_size + 1)])
        self.more_pages = len(results) > page_size
        return results[:page_size]

    def get_paginated_response(self, data):
        return Response(collections.OrderedDict([
            ('next', self.get_next_link(data)),
            #('previous', self.get_previous_link(data)),
            ('results', data)
        ]))

    def get_next_link(self, data):
        if not self.more_pages:
            return None
        url = self.request and self.request.get_full_path() or ''
        url = url.encode('utf-8')
        return replace_query_param(url, 'after', data[-1][self.order_by])

    def get_previous_link(self, data):
        url = self.request.build_absolute_uri()
        return url

    def get_paginated_response_schema(self, schema):
        return {
            'type': 'object',
            'properties': {
                'next': {
                    'type': 'string',
                    'nullable': True,
                },
                #'previous': {
                #    'type': 'string',
                #    'nullable': True,
                #},
                'results': schema,
            },
        }

    def to_html(self):
        template = loader.get_template(self.template)
        context = self.get_html_context()
        return template.render(context)


class Pagination(pagination.PageNumberPagination):

    page_size_query_param = 'page_size'
    max_page_size = settings.MAX_PAGE_SIZE
    count_disabled = False

    def get_next_link(self):
        if not self.page.has_next():
            return None
        url = self.request and self.request.get_full_path() or ''
        url = url.encode('utf-8')
        page_number = self.page.next_page_number()
        return replace_query_param(self.cap_page_size(url), self.page_query_param, page_number)

    def get_previous_link(self):
        if not self.page.has_previous():
            return None
        url = self.request and self.request.get_full_path() or ''
        url = url.encode('utf-8')
        page_number = self.page.previous_page_number()
        return replace_query_param(self.cap_page_size(url), self.page_query_param, page_number)

    def cap_page_size(self, url):
        if int(self.request.query_params.get(self.page_size_query_param, 0)) > self.max_page_size:
            url = replace_query_param(url, self.page_size_query_param, self.max_page_size)
        return url

    def get_html_context(self):
        context = super().get_html_context()
        context['page_links'] = [pl._replace(url=self.cap_page_size(pl.url))
                                 for pl in context['page_links']]

        return context

    def paginate_queryset(self, queryset, request, **kwargs):
        self.count_disabled = 'count_disabled' in request.query_params
        try:
            if self.count_disabled:
                self.django_paginator_class = DisabledPaginator
            return super(Pagination, self).paginate_queryset(queryset, request, **kwargs)
        finally:
            self.django_paginator_class = DjangoPaginator

    def get_paginated_response(self, data):
        if self.count_disabled:
            return Response({'results': data})
        return super(Pagination, self).get_paginated_response(data)

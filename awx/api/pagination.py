# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Django
from django.core.paginator import Paginator as DjangoPaginator
from django.core.paginator import PageNotAnInteger, EmptyPage
from django.db import connections

# Django REST Framework
from django.conf import settings
from rest_framework import pagination
from rest_framework.utils.urls import replace_query_param


class Paginator(DjangoPaginator):

    def __init__(self, object_list, per_page, orphans=0, allow_empty_first_page=True):
        self.count_field = None
        # Based on http://stackoverflow.com/questions/156114/best-way-to-get-result-count-before-limit-was-applied
        # With PostgreSQL, we can use a window function to include the total
        # count of results (before limit and offset are applied) as an extra
        # column and avoid having to issue a separate COUNT(*) query.
        if hasattr(object_list, 'extra'):
            if connections[getattr(object_list, 'db', None) or 'default'].vendor == 'postgresql':
                object_list = object_list.extra(select=dict(__count='COUNT(*) OVER()'))
                self.count_field = '__count'
        super(Paginator, self).__init__(object_list, per_page, orphans, allow_empty_first_page)
        assert self.orphans == 0

    def validate_number(self, number, check_num_pages=True):
        """
        Validates the given 1-based page number.
        """
        try:
            number = int(number)
        except (TypeError, ValueError):
            raise PageNotAnInteger('That page number is not an integer')
        if number < 1:
            raise EmptyPage('That page number is less than 1')
        # Optionally skip checking num_pages, since that will result in a
        # COUNT(*) query.
        if check_num_pages and number > self.num_pages:
            if number == 1 and self.allow_empty_first_page:
                pass
            else:
                raise EmptyPage('That page contains no results')
        return number

    def page(self, number):
        """
        Returns a Page object for the given 1-based page number.
        """
        number = self.validate_number(number, check_num_pages=bool(self.count_field is None))
        bottom = (number - 1) * self.per_page
        top = bottom + self.per_page
        sub_list = self.object_list[bottom:top]
        if self.count_field and self._count is None:
            # Execute one query to fetch all results.
            sub_list = list(sub_list)
            try:
                # Get the total count from the first result.
                self._count = getattr(sub_list[0], self.count_field)
            except IndexError:
                # If no results were returned, we still don't know the total
                # count, but do know that we've reached an empty page.
                if number > 1 or not self.allow_empty_first_page:
                    raise EmptyPage('That page contains no results')
        return self._get_page(sub_list, number, self)


class Pagination(pagination.PageNumberPagination):

    page_size_query_param = 'page_size'
    max_page_size = settings.MAX_PAGE_SIZE
    django_paginator_class = Paginator

    def get_next_link(self):
        if not self.page.has_next():
            return None
        url = self.request and self.request.get_full_path() or ''
        url = url.encode('utf-8')
        page_number = self.page.next_page_number()
        return replace_query_param(url, self.page_query_param, page_number)

    def get_previous_link(self):
        if not self.page.has_previous():
            return None
        url = self.request and self.request.get_full_path() or ''
        url = url.encode('utf-8')
        page_number = self.page.previous_page_number()
        return replace_query_param(url, self.page_query_param, page_number)

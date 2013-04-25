# Copyright (c) 2013 AnsibleWorks, Inc.
#
# This file is part of Ansible Commander.
# 
# Ansible Commander is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License. 
#
# Ansible Commander is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Ansible Commander. If not, see <http://www.gnu.org/licenses/>.

from rest_framework.filters import BaseFilterBackend
from django.core.exceptions import PermissionDenied

# TODO: does order_by still work?

class CustomFilterBackend(object):

    def filter_queryset(self, request, queryset, view):

        keys = request.GET.keys()

        terms = {}
        order_by = None

        for key in keys:

            value = request.GET[key]

            if key in [ 'page', 'page_size' ]:
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

# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.urls import re_path

from awx.api.views import (
    ReceptorAddressesList,
    ReceptorAddressDetail,
)


urls = [
    re_path(r'^$', ReceptorAddressesList.as_view(), name='receptor_addresses_list'),
    re_path(r'^(?P<pk>[0-9]+)/$', ReceptorAddressDetail.as_view(), name='receptor_address_detail'),
]

__all__ = ['urls']

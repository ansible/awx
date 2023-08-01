# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.urls import re_path

from awx.api.views.inventory import (
    ConstructedInventoryDetail,
    ConstructedInventoryList,
)


urls = [
    re_path(r'^$', ConstructedInventoryList.as_view(), name='constructed_inventory_list'),
    re_path(r'^(?P<pk>[0-9]+)/$', ConstructedInventoryDetail.as_view(), name='constructed_inventory_detail'),
]

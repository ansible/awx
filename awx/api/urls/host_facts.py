# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.urls import re_path

from awx.api.views import HostAnsibleFactsList, HostAnsibleFactsDetail

urls = [
    re_path(r'^$', HostAnsibleFactsList.as_view(), name='host_ansible_facts_list'),
    re_path(r'^(?P<pk>[0-9]+)/$', HostAnsibleFactsDetail.as_view(), name='host_ansible_facts_detail'),
]

__all__ = ['urls']

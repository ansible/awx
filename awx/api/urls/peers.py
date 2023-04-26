# Copyright (c) 2017 Ansible, Inc.
# All Rights Reserved.

from django.urls import re_path

from awx.api.views import PeersList, PeersDetail


urls = [
    re_path(r'^$', PeersList.as_view(), name='peers_list'),
    re_path(r'^(?P<pk>[0-9]+)/$', PeersDetail.as_view(), name='peers_detail'),
]

__all__ = ['urls']

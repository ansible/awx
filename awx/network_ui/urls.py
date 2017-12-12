# Copyright (c) 2017 Red Hat, Inc
from django.conf.urls import include, url
import sys

from . import views
import awx.network_ui.routing

app_name = 'network_ui'
urlpatterns = [
    url(r'^download_trace$', views.download_trace, name='download_trace'),
    url(r'^topology.json$', views.json_topology_data, name='json_topology_data'),
    url(r'^topology.yaml$', views.yaml_topology_data, name='json_topology_data'),
    url(r'^$', views.index, name='index'),
]


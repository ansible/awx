# Copyright (c) 2017 Red Hat, Inc
from django.conf.urls import url

from awx.network_ui import views

app_name = 'network_ui'
urlpatterns = [
    url(r'^topology.json$', views.json_topology_data, name='json_topology_data'),
    url(r'^topology.yaml$', views.yaml_topology_data, name='json_topology_data'),
]

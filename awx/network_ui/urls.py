from django.conf.urls import include, url
import sys

from . import views
import awx.network_ui.routing

app_name = 'network_ui'
urlpatterns = [
    url(r'^topology_json$', views.json_topology_data, name='json_topology_data'),
    url(r'^topology_yaml$', views.yaml_topology_data, name='json_topology_data'),
    url(r'^$', views.index, name='index'),
]


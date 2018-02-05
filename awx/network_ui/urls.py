# Copyright (c) 2017 Red Hat, Inc
from django.conf.urls import url, include

import awx.api.urls

from awx.network_ui import views
from awx.network_ui import v2_api_views

app_name = 'network_ui'
urlpatterns = [
    url(r'^tests$', views.tests, name='tests'),
    url(r'^upload_test$', views.upload_test, name='upload_test'),
    url(r'^download_coverage/(?P<pk>[0-9]+)$', views.download_coverage, name='download_coverage'),
    url(r'^download_trace$', views.download_trace, name='download_trace'),
    url(r'^download_recording$', views.download_recording, name='download_recording'),
    url(r'^topology.json$', views.json_topology_data, name='json_topology_data'),
    url(r'^topology.yaml$', views.yaml_topology_data, name='json_topology_data'),
]


v2_api_urlpatterns = [
    url(r'^hosts/(?P<host_id>[0-9]+)/device/$',
        v2_api_views.DeviceViewSet.as_view({'get': 'retrieve', 'post': 'create', 'delete': 'destroy', 'put': 'update'}),
        name="host_device_detail"),
    url(r'^hosts/(?P<host_id>[0-9]+)/device/interfaces/$',
        v2_api_views.InterfaceViewSet.as_view({'get': 'list', 'post': 'create'}),
        name="host_device_interfaces_list"),
    url(r'^hosts/(?P<host_id>[0-9]+)/device/interfaces/(?P<pk>[0-9]+)/$',
        v2_api_views.InterfaceViewSet.as_view({'get': 'retrieve', 'post': 'update', 'delete': 'destroy', 'put': 'update'}),
        name="host_device_interfaces_detail"),
    url(r'^inventories/(?P<inventory_id>[0-9]+)/links/$',
        v2_api_views.LinkViewSet.as_view({'get': 'list', 'post': 'create'}),
        name="inventory_links_list"),
    url(r'^inventories/(?P<inventory_id>[0-9]+)/links/(?P<pk>[0-9]+)/$',
        v2_api_views.LinkViewSet.as_view({'get': 'retrieve', 'post': 'update', 'delete': 'destroy', 'put': 'update'}),
        name="inventory_links_detail"),
    url(r'^inventories/(?P<inventory_id>[0-9]+)/topology/$',
        v2_api_views.TopologyViewSet.as_view({'get': 'list', 'post': 'create'}),
        name="inventory_topology_detail"),
    url(r'^groups/(?P<group_id>[0-9]+)/group/$',
        v2_api_views.GroupViewSet.as_view({'get': 'list', 'post': 'create'}),
        name="group_group_detail"),
    url(r'^toolbox/$',
        v2_api_views.ToolboxViewSet.as_view({'get': 'list', 'post': 'create'}),
        name="toolbox_list"),
    url(r'^toolbox/(?P<pk>[0-9]+)/$',
        v2_api_views.ToolboxViewSet.as_view({'get': 'retrieve', 'post': 'update', 'delete': 'destroy', 'put': 'update'}),
        name="toolbox_detail"),
    url(r'^toolboxitem/$',
        v2_api_views.ToolboxItemViewSet.as_view({'get': 'list', 'post': 'create'}),
        name="toolbox_item_list"),
    url(r'^toolboxitem/(?P<pk>[0-9]+)/$',
        v2_api_views.ToolboxItemViewSet.as_view({'get': 'retrieve', 'post': 'update', 'delete': 'destroy', 'put': 'update'}),
        name="toolbox_item_detail"),
]

urlpatterns += [
    url(r'^api/(?P<version>(v2))/', include(v2_api_urlpatterns))
]
awx.api.urls.urlpatterns += [
    url(r'^(?P<version>(v2))/', include(v2_api_urlpatterns))
]


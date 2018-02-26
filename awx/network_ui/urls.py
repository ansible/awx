# Copyright (c) 2017 Red Hat, Inc
from django.conf.urls import url, include

import awx.api.urls

from awx.network_ui import views
from awx.network_ui import v1_api_urls
from awx.network_ui import v2_api_urls

import awx.network_ui.v2_api_access

app_name = 'network_ui'
urlpatterns = [
    url(r'^tests$', views.tests, name='tests'),
    url(r'^upload_test$', views.upload_test, name='upload_test'),
    url(r'^download_coverage/(?P<pk>[0-9]+)$', views.download_coverage, name='download_coverage'),
    url(r'^download_trace$', views.download_trace, name='download_trace'),
    url(r'^download_recording$', views.download_recording, name='download_recording'),
    url(r'^topology.json$', views.json_topology_data, name='json_topology_data'),
    url(r'^topology.yaml$', views.yaml_topology_data, name='json_topology_data'),
    url(r'^api/v1/', include(v1_api_urls.router.urls)),
]

urlpatterns += [
    url(r'^api/(?P<version>(v2))/canvas/', include(v2_api_urls.urls))
]
awx.api.urls.urlpatterns += [
    url(r'^(?P<version>(v2))/canvas/', include(v2_api_urls.urls))
]


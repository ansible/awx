from rest_framework import routers
from django.conf.urls import url

from awx.network_ui.v2_api_views import (DeviceList, DeviceDetail)
from awx.network_ui.v2_api_views import (LinkList, LinkDetail)
from awx.network_ui.v2_api_views import (TopologyList, TopologyDetail)
from awx.network_ui.v2_api_views import (InterfaceList, InterfaceDetail)
from awx.network_ui.v2_api_views import (GroupList, GroupDetail)
from awx.network_ui.v2_api_views import (GroupDeviceList, GroupDeviceDetail)
from awx.network_ui.v2_api_views import (StreamList, StreamDetail)
from awx.network_ui.v2_api_views import (ProcessList, ProcessDetail)
from awx.network_ui.v2_api_views import (ToolboxList, ToolboxDetail)
from awx.network_ui.v2_api_views import (ToolboxItemList, ToolboxItemDetail)
from awx.network_ui.v2_api_views import (TopologyInventoryList, TopologyInventoryDetail)


urls = []


urls += [
    url(r'^device/$', DeviceList.as_view(), name='canvas_device_list'),
    url(r'^device/(?P<pk>[0-9]+)/$', DeviceDetail.as_view(), name='canvas_device_detail'),
]

urls += [
    url(r'^link/$', LinkList.as_view(), name='canvas_link_list'),
    url(r'^link/(?P<pk>[0-9]+)/$', LinkDetail.as_view(), name='canvas_link_detail'),
]

urls += [
    url(r'^topology/$', TopologyList.as_view(), name='canvas_topology_list'),
    url(r'^topology/(?P<pk>[0-9]+)/$', TopologyDetail.as_view(), name='canvas_topology_detail'),
]

urls += [
    url(r'^interface/$', InterfaceList.as_view(), name='canvas_interface_list'),
    url(r'^interface/(?P<pk>[0-9]+)/$', InterfaceDetail.as_view(), name='canvas_interface_detail'),
]

urls += [
    url(r'^group/$', GroupList.as_view(), name='canvas_group_list'),
    url(r'^group/(?P<pk>[0-9]+)/$', GroupDetail.as_view(), name='canvas_group_detail'),
]

urls += [
    url(r'^groupdevice/$', GroupDeviceList.as_view(), name='canvas_groupdevice_list'),
    url(r'^groupdevice/(?P<pk>[0-9]+)/$', GroupDeviceDetail.as_view(), name='canvas_groupdevice_detail'),
]

urls += [
    url(r'^stream/$', StreamList.as_view(), name='canvas_stream_list'),
    url(r'^stream/(?P<pk>[0-9]+)/$', StreamDetail.as_view(), name='canvas_stream_detail'),
]

urls += [
    url(r'^process/$', ProcessList.as_view(), name='canvas_process_list'),
    url(r'^process/(?P<pk>[0-9]+)/$', ProcessDetail.as_view(), name='canvas_process_detail'),
]

urls += [
    url(r'^toolbox/$', ToolboxList.as_view(), name='canvas_toolbox_list'),
    url(r'^toolbox/(?P<pk>[0-9]+)/$', ToolboxDetail.as_view(), name='canvas_toolbox_detail'),
]

urls += [
    url(r'^toolboxitem/$', ToolboxItemList.as_view(), name='canvas_toolboxitem_list'),
    url(r'^toolboxitem/(?P<pk>[0-9]+)/$', ToolboxItemDetail.as_view(), name='canvas_toolboxitem_detail'),
]

urls += [
    url(r'^topologyinventory/$', TopologyInventoryList.as_view(), name='canvas_topologyinventory_list'),
    url(r'^topologyinventory/(?P<pk>[0-9]+)/$', TopologyInventoryDetail.as_view(), name='canvas_topologyinventory_detail'),
]

__all__ = ['urls']

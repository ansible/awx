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
    url(r'^device/$', DeviceList.as_view(), name='device_list'),
    url(r'^device/(?P<pk>[0-9]+)/$', DeviceDetail.as_view(), name='device_detail'),
]

urls += [
    url(r'^link/$', LinkList.as_view(), name='link_list'),
    url(r'^link/(?P<pk>[0-9]+)/$', LinkDetail.as_view(), name='link_detail'),
]

urls += [
    url(r'^topology/$', TopologyList.as_view(), name='topology_list'),
    url(r'^topology/(?P<pk>[0-9]+)/$', TopologyDetail.as_view(), name='topology_detail'),
]

urls += [
    url(r'^interface/$', InterfaceList.as_view(), name='interface_list'),
    url(r'^interface/(?P<pk>[0-9]+)/$', InterfaceDetail.as_view(), name='interface_detail'),
]

urls += [
    url(r'^group/$', GroupList.as_view(), name='group_list'),
    url(r'^group/(?P<pk>[0-9]+)/$', GroupDetail.as_view(), name='group_detail'),
]

urls += [
    url(r'^groupdevice/$', GroupDeviceList.as_view(), name='groupdevice_list'),
    url(r'^groupdevice/(?P<pk>[0-9]+)/$', GroupDeviceDetail.as_view(), name='groupdevice_detail'),
]

urls += [
    url(r'^stream/$', StreamList.as_view(), name='stream_list'),
    url(r'^stream/(?P<pk>[0-9]+)/$', StreamDetail.as_view(), name='stream_detail'),
]

urls += [
    url(r'^process/$', ProcessList.as_view(), name='process_list'),
    url(r'^process/(?P<pk>[0-9]+)/$', ProcessDetail.as_view(), name='process_detail'),
]

urls += [
    url(r'^toolbox/$', ToolboxList.as_view(), name='toolbox_list'),
    url(r'^toolbox/(?P<pk>[0-9]+)/$', ToolboxDetail.as_view(), name='toolbox_detail'),
]

urls += [
    url(r'^toolboxitem/$', ToolboxItemList.as_view(), name='toolboxitem_list'),
    url(r'^toolboxitem/(?P<pk>[0-9]+)/$', ToolboxItemDetail.as_view(), name='toolboxitem_detail'),
]

urls += [
    url(r'^topologyinventory/$', TopologyInventoryList.as_view(), name='topologyinventory_list'),
    url(r'^topologyinventory/(?P<pk>[0-9]+)/$', TopologyInventoryDetail.as_view(), name='topologyinventory_detail'),
]

__all__ = ['urls']

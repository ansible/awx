from rest_framework import viewsets

from awx.network_ui.models import Device
from awx.network_ui.models import Link
from awx.network_ui.models import Topology
from awx.network_ui.models import Interface
from awx.network_ui.models import Group
from awx.network_ui.models import GroupDevice
from awx.network_ui.models import Stream
from awx.network_ui.models import Process
from awx.network_ui.models import Toolbox
from awx.network_ui.models import ToolboxItem
from awx.network_ui.models import TopologyInventory

from awx.network_ui.v1_api_serializers import DeviceSerializer
from awx.network_ui.v1_api_serializers import LinkSerializer
from awx.network_ui.v1_api_serializers import TopologySerializer
from awx.network_ui.v1_api_serializers import InterfaceSerializer
from awx.network_ui.v1_api_serializers import GroupSerializer
from awx.network_ui.v1_api_serializers import GroupDeviceSerializer
from awx.network_ui.v1_api_serializers import StreamSerializer
from awx.network_ui.v1_api_serializers import ProcessSerializer
from awx.network_ui.v1_api_serializers import ToolboxSerializer
from awx.network_ui.v1_api_serializers import ToolboxItemSerializer
from awx.network_ui.v1_api_serializers import TopologyInventorySerializer


class DeviceViewSet(viewsets.ModelViewSet):

    queryset = Device.objects.all()
    serializer_class = DeviceSerializer


class LinkViewSet(viewsets.ModelViewSet):

    queryset = Link.objects.all()
    serializer_class = LinkSerializer


class TopologyViewSet(viewsets.ModelViewSet):

    queryset = Topology.objects.all()
    serializer_class = TopologySerializer


class InterfaceViewSet(viewsets.ModelViewSet):

    queryset = Interface.objects.all()
    serializer_class = InterfaceSerializer


class GroupViewSet(viewsets.ModelViewSet):

    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class GroupDeviceViewSet(viewsets.ModelViewSet):

    queryset = GroupDevice.objects.all()
    serializer_class = GroupDeviceSerializer


class StreamViewSet(viewsets.ModelViewSet):

    queryset = Stream.objects.all()
    serializer_class = StreamSerializer


class ProcessViewSet(viewsets.ModelViewSet):

    queryset = Process.objects.all()
    serializer_class = ProcessSerializer


class ToolboxViewSet(viewsets.ModelViewSet):

    queryset = Toolbox.objects.all()
    serializer_class = ToolboxSerializer


class ToolboxItemViewSet(viewsets.ModelViewSet):

    queryset = ToolboxItem.objects.all()
    serializer_class = ToolboxItemSerializer


class TopologyInventoryViewSet(viewsets.ModelViewSet):

    queryset = TopologyInventory.objects.all()
    serializer_class = TopologyInventorySerializer

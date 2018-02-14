from awx.api.generics import ListCreateAPIView
from awx.api.generics import RetrieveUpdateDestroyAPIView

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

from awx.network_ui.v2_api_serializers import DeviceSerializer
from awx.network_ui.v2_api_serializers import LinkSerializer
from awx.network_ui.v2_api_serializers import TopologySerializer
from awx.network_ui.v2_api_serializers import InterfaceSerializer
from awx.network_ui.v2_api_serializers import GroupSerializer
from awx.network_ui.v2_api_serializers import GroupDeviceSerializer
from awx.network_ui.v2_api_serializers import StreamSerializer
from awx.network_ui.v2_api_serializers import ProcessSerializer
from awx.network_ui.v2_api_serializers import ToolboxSerializer
from awx.network_ui.v2_api_serializers import ToolboxItemSerializer
from awx.network_ui.v2_api_serializers import TopologyInventorySerializer


class DeviceList(ListCreateAPIView):

    model = Device
    serializer_class = DeviceSerializer


class DeviceDetail(RetrieveUpdateDestroyAPIView):

    model = Device
    serializer_class = DeviceSerializer


class LinkList(ListCreateAPIView):

    model = Link
    serializer_class = LinkSerializer


class LinkDetail(RetrieveUpdateDestroyAPIView):

    model = Link
    serializer_class = LinkSerializer


class TopologyList(ListCreateAPIView):

    model = Topology
    serializer_class = TopologySerializer


class TopologyDetail(RetrieveUpdateDestroyAPIView):

    model = Topology
    serializer_class = TopologySerializer


class InterfaceList(ListCreateAPIView):

    model = Interface
    serializer_class = InterfaceSerializer


class InterfaceDetail(RetrieveUpdateDestroyAPIView):

    model = Interface
    serializer_class = InterfaceSerializer


class GroupList(ListCreateAPIView):

    model = Group
    serializer_class = GroupSerializer


class GroupDetail(RetrieveUpdateDestroyAPIView):

    model = Group
    serializer_class = GroupSerializer


class GroupDeviceList(ListCreateAPIView):

    model = GroupDevice
    serializer_class = GroupDeviceSerializer


class GroupDeviceDetail(RetrieveUpdateDestroyAPIView):

    model = GroupDevice
    serializer_class = GroupDeviceSerializer


class StreamList(ListCreateAPIView):

    model = Stream
    serializer_class = StreamSerializer


class StreamDetail(RetrieveUpdateDestroyAPIView):

    model = Stream
    serializer_class = StreamSerializer


class ProcessList(ListCreateAPIView):

    model = Process
    serializer_class = ProcessSerializer


class ProcessDetail(RetrieveUpdateDestroyAPIView):

    model = Process
    serializer_class = ProcessSerializer


class ToolboxList(ListCreateAPIView):

    model = Toolbox
    serializer_class = ToolboxSerializer


class ToolboxDetail(RetrieveUpdateDestroyAPIView):

    model = Toolbox
    serializer_class = ToolboxSerializer


class ToolboxItemList(ListCreateAPIView):

    model = ToolboxItem
    serializer_class = ToolboxItemSerializer


class ToolboxItemDetail(RetrieveUpdateDestroyAPIView):

    model = ToolboxItem
    serializer_class = ToolboxItemSerializer


class TopologyInventoryList(ListCreateAPIView):

    model = TopologyInventory
    serializer_class = TopologyInventorySerializer


class TopologyInventoryDetail(RetrieveUpdateDestroyAPIView):

    model = TopologyInventory
    serializer_class = TopologyInventorySerializer

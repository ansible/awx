from awx.main.access import BaseAccess, access_registry

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


class DeviceAccess(BaseAccess):

    model = Device


access_registry[Device] = DeviceAccess


class LinkAccess(BaseAccess):

    model = Link


access_registry[Link] = LinkAccess


class TopologyAccess(BaseAccess):

    model = Topology


access_registry[Topology] = TopologyAccess


class InterfaceAccess(BaseAccess):

    model = Interface


access_registry[Interface] = InterfaceAccess


class GroupAccess(BaseAccess):

    model = Group


access_registry[Group] = GroupAccess


class GroupDeviceAccess(BaseAccess):

    model = GroupDevice


access_registry[GroupDevice] = GroupDeviceAccess


class StreamAccess(BaseAccess):

    model = Stream


access_registry[Stream] = StreamAccess


class ProcessAccess(BaseAccess):

    model = Process


access_registry[Process] = ProcessAccess


class ToolboxAccess(BaseAccess):

    model = Toolbox


access_registry[Toolbox] = ToolboxAccess


class ToolboxItemAccess(BaseAccess):

    model = ToolboxItem


access_registry[ToolboxItem] = ToolboxItemAccess


class TopologyInventoryAccess(BaseAccess):

    model = TopologyInventory


access_registry[TopologyInventory] = TopologyInventoryAccess

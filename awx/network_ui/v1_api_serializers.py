from awx.api.serializers import BaseSerializer

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


class DeviceSerializer(BaseSerializer):
    class Meta:
        model = Device
        fields = ('device_id',
                  'topology',
                  'name',
                  'x',
                  'y',
                  'id',
                  'device_type',
                  'interface_id_seq',
                  'process_id_seq',
                  'host_id')


class LinkSerializer(BaseSerializer):
    class Meta:
        model = Link
        fields = ('link_id',
                  'from_device',
                  'to_device',
                  'from_interface',
                  'to_interface',
                  'id',
                  'name')


class TopologySerializer(BaseSerializer):
    class Meta:
        model = Topology
        fields = ('topology_id',
                  'name',
                  'scale',
                  'panX',
                  'panY',
                  'device_id_seq',
                  'link_id_seq',
                  'group_id_seq',
                  'stream_id_seq')


class InterfaceSerializer(BaseSerializer):
    class Meta:
        model = Interface
        fields = ('interface_id',
                  'device',
                  'name',
                  'id')


class GroupSerializer(BaseSerializer):
    class Meta:
        model = Group
        fields = ('group_id',
                  'id',
                  'name',
                  'x1',
                  'y1',
                  'x2',
                  'y2',
                  'topology',
                  'group_type',
                  'inventory_group_id')


class GroupDeviceSerializer(BaseSerializer):
    class Meta:
        model = GroupDevice
        fields = ('group_device_id',
                  'group',
                  'device')


class StreamSerializer(BaseSerializer):
    class Meta:
        model = Stream
        fields = ('stream_id',
                  'from_device',
                  'to_device',
                  'label',
                  'id')


class ProcessSerializer(BaseSerializer):
    class Meta:
        model = Process
        fields = ('process_id',
                  'device',
                  'name',
                  'process_type',
                  'id')


class ToolboxSerializer(BaseSerializer):
    class Meta:
        model = Toolbox
        fields = ('toolbox_id',
                  'name')


class ToolboxItemSerializer(BaseSerializer):
    class Meta:
        model = ToolboxItem
        fields = ('toolbox_item_id',
                  'toolbox',
                  'data')


class TopologyInventorySerializer(BaseSerializer):
    class Meta:
        model = TopologyInventory
        fields = ('topology_inventory_id',
                  'topology',
                  'inventory_id')

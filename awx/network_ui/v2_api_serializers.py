from rest_framework import serializers

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


class DeviceSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="network_ui:device-detail", lookup_field='pk')

    topology = serializers.HyperlinkedRelatedField(view_name="network_ui:topology-detail", lookup_field="pk", read_only=True)

    class Meta:
        model = Device
        fields = ('url', 'device_id', 'topology', 'name', 'x', 'y', 'id', 'type', 'interface_id_seq', 'process_id_seq', 'host_id',)


class LinkSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="network_ui:link-detail", lookup_field='pk')

    from_device = serializers.HyperlinkedRelatedField(view_name="network_ui:device-detail", lookup_field="pk", read_only=True)

    to_device = serializers.HyperlinkedRelatedField(view_name="network_ui:device-detail", lookup_field="pk", read_only=True)

    from_interface = serializers.HyperlinkedRelatedField(view_name="network_ui:interface-detail", lookup_field="pk", read_only=True)

    to_interface = serializers.HyperlinkedRelatedField(view_name="network_ui:interface-detail", lookup_field="pk", read_only=True)

    class Meta:
        model = Link
        fields = ('url', 'link_id', 'from_device', 'to_device', 'from_interface', 'to_interface', 'id', 'name',)


class TopologySerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="network_ui:topology-detail", lookup_field='pk')

    class Meta:
        model = Topology
        fields = ('url', 'topology_id', 'name', 'scale', 'panX', 'panY', 'device_id_seq', 'link_id_seq', 'group_id_seq', 'stream_id_seq',)


class InterfaceSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="network_ui:interface-detail", lookup_field='pk')

    device = serializers.HyperlinkedRelatedField(view_name="network_ui:device-detail", lookup_field="pk", read_only=True)

    class Meta:
        model = Interface
        fields = ('url', 'interface_id', 'device', 'name', 'id',)


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="network_ui:group-detail", lookup_field='pk')

    topology = serializers.HyperlinkedRelatedField(view_name="network_ui:topology-detail", lookup_field="pk", read_only=True)

    class Meta:
        model = Group
        fields = ('url', 'group_id', 'id', 'name', 'x1', 'y1', 'x2', 'y2', 'topology', 'type',)


class GroupDeviceSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="network_ui:groupdevice-detail", lookup_field='pk')

    group = serializers.HyperlinkedRelatedField(view_name="network_ui:group-detail", lookup_field="pk", read_only=True)

    device = serializers.HyperlinkedRelatedField(view_name="network_ui:device-detail", lookup_field="pk", read_only=True)

    class Meta:
        model = GroupDevice
        fields = ('url', 'group_device_id', 'group', 'device',)


class StreamSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="network_ui:stream-detail", lookup_field='pk')

    stream_id = serializers.HyperlinkedRelatedField(view_name="network_ui:stream-detail", lookup_field="pk", read_only=True)

    from_device = serializers.HyperlinkedRelatedField(view_name="network_ui:device-detail", lookup_field="pk", read_only=True)

    to_device = serializers.HyperlinkedRelatedField(view_name="network_ui:device-detail", lookup_field="pk", read_only=True)

    class Meta:
        model = Stream
        fields = ('url', 'stream_id', 'from_device', 'to_device', 'label', 'id',)


class ProcessSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="network_ui:process-detail", lookup_field='pk')

    device = serializers.HyperlinkedRelatedField(view_name="network_ui:device-detail", lookup_field="pk", read_only=True)

    class Meta:
        model = Process
        fields = ('url', 'process_id', 'device', 'name', 'type', 'id',)


class ToolboxSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="network_ui:toolbox-detail", lookup_field='pk')

    class Meta:
        model = Toolbox
        fields = ('url', 'toolbox_id', 'name',)


class ToolboxItemSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="network_ui:toolboxitem-detail", lookup_field='pk')

    toolbox = serializers.HyperlinkedRelatedField(view_name="network_ui:toolbox-detail", lookup_field="pk", read_only=True)

    class Meta:
        model = ToolboxItem
        fields = ('url', 'toolbox_item_id', 'toolbox', 'data',)


class TopologyInventorySerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="network_ui:topologyinventory-detail", lookup_field='pk')

    topology = serializers.HyperlinkedRelatedField(view_name="network_ui:topology-detail", lookup_field="pk", read_only=True)

    class Meta:
        model = TopologyInventory
        fields = ('url', 'topology_inventory_id', 'topology', 'inventory_id',)

from rest_framework import serializers

from awx.network_ui.models import Device
from awx.network_ui.models import Link
from awx.network_ui.models import Topology
from awx.network_ui.models import Client
from awx.network_ui.models import TopologyHistory
from awx.network_ui.models import MessageType
from awx.network_ui.models import Interface
from awx.network_ui.models import Group
from awx.network_ui.models import GroupDevice
from awx.network_ui.models import DataBinding
from awx.network_ui.models import DataType
from awx.network_ui.models import DataSheet
from awx.network_ui.models import Stream
from awx.network_ui.models import Process
from awx.network_ui.models import Toolbox
from awx.network_ui.models import ToolboxItem
from awx.network_ui.models import FSMTrace
from awx.network_ui.models import TopologyInventory
from awx.network_ui.models import EventTrace
from awx.network_ui.models import Coverage
from awx.network_ui.models import TopologySnapshot
from awx.network_ui.models import TestCase
from awx.network_ui.models import Result
from awx.network_ui.models import CodeUnderTest
from awx.network_ui.models import TestResult


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


class ClientSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="network_ui:client-detail", lookup_field='pk')

    class Meta:
        model = Client
        fields = ('url', 'client_id',)


class TopologyHistorySerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="network_ui:topologyhistory-detail", lookup_field='pk')

    topology = serializers.HyperlinkedRelatedField(view_name="network_ui:topology-detail", lookup_field="pk", read_only=True)

    client = serializers.HyperlinkedRelatedField(view_name="network_ui:client-detail", lookup_field="pk", read_only=True)

    message_type = serializers.HyperlinkedRelatedField(view_name="network_ui:messagetype-detail", lookup_field="pk", read_only=True)

    class Meta:
        model = TopologyHistory
        fields = ('url', 'topology_history_id', 'topology', 'client', 'message_type', 'message_id', 'message_data', 'undone',)


class MessageTypeSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="network_ui:messagetype-detail", lookup_field='pk')

    class Meta:
        model = MessageType
        fields = ('url', 'message_type_id', 'name',)


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


class DataBindingSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="network_ui:databinding-detail", lookup_field='pk')

    data_type = serializers.HyperlinkedRelatedField(view_name="network_ui:datatype-detail", lookup_field="pk", read_only=True)

    sheet = serializers.HyperlinkedRelatedField(view_name="network_ui:datasheet-detail", lookup_field="pk", read_only=True)

    class Meta:
        model = DataBinding
        fields = ('url', 'data_binding_id', 'column', 'row', 'table', 'primary_key_id', 'field', 'data_type', 'sheet',)


class DataTypeSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="network_ui:datatype-detail", lookup_field='pk')

    class Meta:
        model = DataType
        fields = ('url', 'data_type_id', 'type_name',)


class DataSheetSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="network_ui:datasheet-detail", lookup_field='pk')

    topology = serializers.HyperlinkedRelatedField(view_name="network_ui:topology-detail", lookup_field="pk", read_only=True)

    client = serializers.HyperlinkedRelatedField(view_name="network_ui:client-detail", lookup_field="pk", read_only=True)

    class Meta:
        model = DataSheet
        fields = ('url', 'data_sheet_id', 'name', 'topology', 'client',)


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


class FSMTraceSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="network_ui:fsmtrace-detail", lookup_field='pk')

    client = serializers.HyperlinkedRelatedField(view_name="network_ui:client-detail", lookup_field="pk", read_only=True)

    class Meta:
        model = FSMTrace
        fields = ('url', 'fsm_trace_id', 'fsm_name', 'from_state', 'to_state', 'message_type', 'client', 'trace_session_id', 'order',)


class TopologyInventorySerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="network_ui:topologyinventory-detail", lookup_field='pk')

    topology = serializers.HyperlinkedRelatedField(view_name="network_ui:topology-detail", lookup_field="pk", read_only=True)

    class Meta:
        model = TopologyInventory
        fields = ('url', 'topology_inventory_id', 'topology', 'inventory_id',)


class EventTraceSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="network_ui:eventtrace-detail", lookup_field='pk')

    client = serializers.HyperlinkedRelatedField(view_name="network_ui:client-detail", lookup_field="pk", read_only=True)

    class Meta:
        model = EventTrace
        fields = ('url', 'event_trace_id', 'client', 'trace_session_id', 'event_data', 'message_id',)


class CoverageSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="network_ui:coverage-detail", lookup_field='pk')

    test_result = serializers.HyperlinkedRelatedField(view_name="network_ui:testresult-detail", lookup_field="pk", read_only=True)

    class Meta:
        model = Coverage
        fields = ('url', 'coverage_id', 'coverage_data', 'test_result',)


class TopologySnapshotSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="network_ui:topologysnapshot-detail", lookup_field='pk')

    client = serializers.HyperlinkedRelatedField(view_name="network_ui:client-detail", lookup_field="pk", read_only=True)

    snapshot_data = serializers.HyperlinkedRelatedField(view_name="network_ui:topologysnapshot-detail", lookup_field="pk", read_only=True)

    class Meta:
        model = TopologySnapshot
        fields = ('url', 'topology_snapshot_id', 'client', 'topology_id', 'trace_session_id', 'snapshot_data', 'order',)


class TestCaseSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="network_ui:testcase-detail", lookup_field='pk')

    name = serializers.HyperlinkedRelatedField(view_name="network_ui:testcase-detail", lookup_field="pk", read_only=True)

    class Meta:
        model = TestCase
        fields = ('url', 'test_case_id', 'name', 'test_case_data',)


class ResultSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="network_ui:result-detail", lookup_field='pk')

    class Meta:
        model = Result
        fields = ('url', 'result_id', 'name',)


class CodeUnderTestSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="network_ui:codeundertest-detail", lookup_field='pk')

    code_under_test_id = serializers.HyperlinkedRelatedField(view_name="network_ui:codeundertest-detail", lookup_field="pk", read_only=True)

    class Meta:
        model = CodeUnderTest
        fields = ('url', 'code_under_test_id', 'version_x', 'version_y', 'version_z', 'commits_since', 'commit_hash',)


class TestResultSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="network_ui:testresult-detail", lookup_field='pk')

    test_case = serializers.HyperlinkedRelatedField(view_name="network_ui:testcase-detail", lookup_field="pk", read_only=True)

    result = serializers.HyperlinkedRelatedField(view_name="network_ui:result-detail", lookup_field="pk", read_only=True)

    code_under_test = serializers.HyperlinkedRelatedField(view_name="network_ui:codeundertest-detail", lookup_field="pk", read_only=True)

    client = serializers.HyperlinkedRelatedField(view_name="network_ui:client-detail", lookup_field="pk", read_only=True)

    class Meta:
        model = TestResult
        fields = ('url', 'test_result_id', 'test_case', 'result', 'code_under_test', 'time', 'id', 'client',)

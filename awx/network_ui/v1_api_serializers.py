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


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ('device_id', 'topology', 'name', 'x', 'y', 'id', 'type', 'interface_id_seq', 'process_id_seq', 'host_id',)


class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Link
        fields = ('link_id', 'from_device', 'to_device', 'from_interface', 'to_interface', 'id', 'name',)


class TopologySerializer(serializers.ModelSerializer):
    class Meta:
        model = Topology
        fields = ('topology_id', 'name', 'scale', 'panX', 'panY', 'device_id_seq', 'link_id_seq', 'group_id_seq', 'stream_id_seq',)


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ('client_id',)


class TopologyHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TopologyHistory
        fields = ('topology_history_id', 'topology', 'client', 'message_type', 'message_id', 'message_data', 'undone',)


class MessageTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageType
        fields = ('message_type_id', 'name',)


class InterfaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interface
        fields = ('interface_id', 'device', 'name', 'id',)


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('group_id', 'id', 'name', 'x1', 'y1', 'x2', 'y2', 'topology', 'type',)


class GroupDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupDevice
        fields = ('group_device_id', 'group', 'device',)


class DataBindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataBinding
        fields = ('data_binding_id', 'column', 'row', 'table', 'primary_key_id', 'field', 'data_type', 'sheet',)


class DataTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataType
        fields = ('data_type_id', 'type_name',)


class DataSheetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSheet
        fields = ('data_sheet_id', 'name', 'topology', 'client',)


class StreamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stream
        fields = ('stream_id', 'from_device', 'to_device', 'label', 'id',)


class ProcessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Process
        fields = ('process_id', 'device', 'name', 'type', 'id',)


class ToolboxSerializer(serializers.ModelSerializer):
    class Meta:
        model = Toolbox
        fields = ('toolbox_id', 'name',)


class ToolboxItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ToolboxItem
        fields = ('toolbox_item_id', 'toolbox', 'data',)


class FSMTraceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FSMTrace
        fields = ('fsm_trace_id', 'fsm_name', 'from_state', 'to_state', 'message_type', 'client', 'trace_session_id', 'order',)


class TopologyInventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TopologyInventory
        fields = ('topology_inventory_id', 'topology', 'inventory_id',)


class EventTraceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventTrace
        fields = ('event_trace_id', 'client', 'trace_session_id', 'event_data', 'message_id',)


class CoverageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coverage
        fields = ('coverage_id', 'coverage_data', 'test_result',)


class TopologySnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TopologySnapshot
        fields = ('topology_snapshot_id', 'client', 'topology_id', 'trace_session_id', 'snapshot_data', 'order',)


class TestCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestCase
        fields = ('test_case_id', 'name', 'test_case_data',)


class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Result
        fields = ('result_id', 'name',)


class CodeUnderTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeUnderTest
        fields = ('code_under_test_id', 'version_x', 'version_y', 'version_z', 'commits_since', 'commit_hash',)


class TestResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestResult
        fields = ('test_result_id', 'test_case', 'result', 'code_under_test', 'time', 'id', 'client',)

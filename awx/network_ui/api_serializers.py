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
        fields = ('topology', 'name', 'x', 'y', 'id', 'type', 'interface_id_seq', 'process_id_seq', 'host_id',)


class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Link
        fields = ('from_device', 'to_device', 'from_interface', 'to_interface', 'id', 'name',)


class TopologySerializer(serializers.ModelSerializer):
    class Meta:
        model = Topology
        fields = ('name', 'scale', 'panX', 'panY', 'device_id_seq', 'link_id_seq', 'group_id_seq', 'stream_id_seq',)


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ()


class TopologyHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TopologyHistory
        fields = ('topology', 'client', 'message_type', 'message_id', 'message_data', 'undone',)


class MessageTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageType
        fields = ('name',)


class InterfaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interface
        fields = ('device', 'name', 'id',)


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'name', 'x1', 'y1', 'x2', 'y2', 'topology', 'type',)


class GroupDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupDevice
        fields = ('group', 'device',)


class DataBindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataBinding
        fields = ('column', 'row', 'table', 'primary_key_id', 'field', 'data_type', 'sheet',)


class DataTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataType
        fields = ('type_name',)


class DataSheetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSheet
        fields = ('name', 'topology', 'client',)


class StreamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stream
        fields = ('from_device', 'to_device', 'label', 'id',)


class ProcessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Process
        fields = ('device', 'name', 'type', 'id',)


class ToolboxSerializer(serializers.ModelSerializer):
    class Meta:
        model = Toolbox
        fields = ('name',)


class ToolboxItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ToolboxItem
        fields = ('toolbox', 'data',)


class FSMTraceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FSMTrace
        fields = ('fsm_name', 'from_state', 'to_state', 'message_type', 'client', 'trace_session_id', 'order',)


class TopologyInventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TopologyInventory
        fields = ('topology', 'inventory_id',)


class EventTraceSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventTrace
        fields = ('client', 'trace_session_id', 'event_data', 'message_id',)


class CoverageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coverage
        fields = ('coverage_data', 'test_result',)


class TopologySnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TopologySnapshot
        fields = ('client', 'topology_id', 'trace_session_id', 'snapshot_data', 'order',)


class TestCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestCase
        fields = ('name', 'test_case_data',)


class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Result
        fields = ('name',)


class CodeUnderTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = CodeUnderTest
        fields = ('version_x', 'version_y', 'version_z', 'commits_since', 'commit_hash',)


class TestResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestResult
        fields = ('test_case', 'result', 'code_under_test', 'time', 'id', 'client',)

from rest_framework import viewsets

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

from awx.network_ui.v1_api_serializers import DeviceSerializer
from awx.network_ui.v1_api_serializers import LinkSerializer
from awx.network_ui.v1_api_serializers import TopologySerializer
from awx.network_ui.v1_api_serializers import ClientSerializer
from awx.network_ui.v1_api_serializers import TopologyHistorySerializer
from awx.network_ui.v1_api_serializers import MessageTypeSerializer
from awx.network_ui.v1_api_serializers import InterfaceSerializer
from awx.network_ui.v1_api_serializers import GroupSerializer
from awx.network_ui.v1_api_serializers import GroupDeviceSerializer
from awx.network_ui.v1_api_serializers import DataBindingSerializer
from awx.network_ui.v1_api_serializers import DataTypeSerializer
from awx.network_ui.v1_api_serializers import DataSheetSerializer
from awx.network_ui.v1_api_serializers import StreamSerializer
from awx.network_ui.v1_api_serializers import ProcessSerializer
from awx.network_ui.v1_api_serializers import ToolboxSerializer
from awx.network_ui.v1_api_serializers import ToolboxItemSerializer
from awx.network_ui.v1_api_serializers import FSMTraceSerializer
from awx.network_ui.v1_api_serializers import TopologyInventorySerializer
from awx.network_ui.v1_api_serializers import EventTraceSerializer
from awx.network_ui.v1_api_serializers import CoverageSerializer
from awx.network_ui.v1_api_serializers import TopologySnapshotSerializer
from awx.network_ui.v1_api_serializers import TestCaseSerializer
from awx.network_ui.v1_api_serializers import ResultSerializer
from awx.network_ui.v1_api_serializers import CodeUnderTestSerializer
from awx.network_ui.v1_api_serializers import TestResultSerializer


class DeviceViewSet(viewsets.ModelViewSet):

    queryset = Device.objects.all()
    serializer_class = DeviceSerializer


class LinkViewSet(viewsets.ModelViewSet):

    queryset = Link.objects.all()
    serializer_class = LinkSerializer


class TopologyViewSet(viewsets.ModelViewSet):

    queryset = Topology.objects.all()
    serializer_class = TopologySerializer


class ClientViewSet(viewsets.ModelViewSet):

    queryset = Client.objects.all()
    serializer_class = ClientSerializer


class TopologyHistoryViewSet(viewsets.ModelViewSet):

    queryset = TopologyHistory.objects.all()
    serializer_class = TopologyHistorySerializer


class MessageTypeViewSet(viewsets.ModelViewSet):

    queryset = MessageType.objects.all()
    serializer_class = MessageTypeSerializer


class InterfaceViewSet(viewsets.ModelViewSet):

    queryset = Interface.objects.all()
    serializer_class = InterfaceSerializer


class GroupViewSet(viewsets.ModelViewSet):

    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class GroupDeviceViewSet(viewsets.ModelViewSet):

    queryset = GroupDevice.objects.all()
    serializer_class = GroupDeviceSerializer


class DataBindingViewSet(viewsets.ModelViewSet):

    queryset = DataBinding.objects.all()
    serializer_class = DataBindingSerializer


class DataTypeViewSet(viewsets.ModelViewSet):

    queryset = DataType.objects.all()
    serializer_class = DataTypeSerializer


class DataSheetViewSet(viewsets.ModelViewSet):

    queryset = DataSheet.objects.all()
    serializer_class = DataSheetSerializer


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


class FSMTraceViewSet(viewsets.ModelViewSet):

    queryset = FSMTrace.objects.all()
    serializer_class = FSMTraceSerializer


class TopologyInventoryViewSet(viewsets.ModelViewSet):

    queryset = TopologyInventory.objects.all()
    serializer_class = TopologyInventorySerializer


class EventTraceViewSet(viewsets.ModelViewSet):

    queryset = EventTrace.objects.all()
    serializer_class = EventTraceSerializer


class CoverageViewSet(viewsets.ModelViewSet):

    queryset = Coverage.objects.all()
    serializer_class = CoverageSerializer


class TopologySnapshotViewSet(viewsets.ModelViewSet):

    queryset = TopologySnapshot.objects.all()
    serializer_class = TopologySnapshotSerializer


class TestCaseViewSet(viewsets.ModelViewSet):

    queryset = TestCase.objects.all()
    serializer_class = TestCaseSerializer


class ResultViewSet(viewsets.ModelViewSet):

    queryset = Result.objects.all()
    serializer_class = ResultSerializer


class CodeUnderTestViewSet(viewsets.ModelViewSet):

    queryset = CodeUnderTest.objects.all()
    serializer_class = CodeUnderTestSerializer


class TestResultViewSet(viewsets.ModelViewSet):

    queryset = TestResult.objects.all()
    serializer_class = TestResultSerializer

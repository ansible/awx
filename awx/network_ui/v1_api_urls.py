from rest_framework import routers
from awx.network_ui import v1_api_views


router = routers.DefaultRouter()


router.register(r'device', v1_api_views.DeviceViewSet)
router.register(r'link', v1_api_views.LinkViewSet)
router.register(r'topology', v1_api_views.TopologyViewSet)
router.register(r'client', v1_api_views.ClientViewSet)
router.register(r'topologyhistory', v1_api_views.TopologyHistoryViewSet)
router.register(r'messagetype', v1_api_views.MessageTypeViewSet)
router.register(r'interface', v1_api_views.InterfaceViewSet)
router.register(r'group', v1_api_views.GroupViewSet)
router.register(r'groupdevice', v1_api_views.GroupDeviceViewSet)
router.register(r'databinding', v1_api_views.DataBindingViewSet)
router.register(r'datatype', v1_api_views.DataTypeViewSet)
router.register(r'datasheet', v1_api_views.DataSheetViewSet)
router.register(r'stream', v1_api_views.StreamViewSet)
router.register(r'process', v1_api_views.ProcessViewSet)
router.register(r'toolbox', v1_api_views.ToolboxViewSet)
router.register(r'toolboxitem', v1_api_views.ToolboxItemViewSet)
router.register(r'fsmtrace', v1_api_views.FSMTraceViewSet)
router.register(r'topologyinventory', v1_api_views.TopologyInventoryViewSet)
router.register(r'eventtrace', v1_api_views.EventTraceViewSet)
router.register(r'coverage', v1_api_views.CoverageViewSet)
router.register(r'topologysnapshot', v1_api_views.TopologySnapshotViewSet)
router.register(r'testcase', v1_api_views.TestCaseViewSet)
router.register(r'result', v1_api_views.ResultViewSet)
router.register(r'codeundertest', v1_api_views.CodeUnderTestViewSet)
router.register(r'testresult', v1_api_views.TestResultViewSet)

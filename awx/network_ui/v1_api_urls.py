from rest_framework import routers
from awx.network_ui import v1_api_views


router = routers.DefaultRouter()


router.register(r'device', v1_api_views.DeviceViewSet)
router.register(r'link', v1_api_views.LinkViewSet)
router.register(r'topology', v1_api_views.TopologyViewSet)
router.register(r'interface', v1_api_views.InterfaceViewSet)
router.register(r'group', v1_api_views.GroupViewSet)
router.register(r'groupdevice', v1_api_views.GroupDeviceViewSet)
router.register(r'stream', v1_api_views.StreamViewSet)
router.register(r'process', v1_api_views.ProcessViewSet)
router.register(r'toolbox', v1_api_views.ToolboxViewSet)
router.register(r'toolboxitem', v1_api_views.ToolboxItemViewSet)
router.register(r'topologyinventory', v1_api_views.TopologyInventoryViewSet)

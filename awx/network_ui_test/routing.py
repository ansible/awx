# Copyright (c) 2017 Red Hat, Inc
from channels.routing import route
from awx.network_ui_test.consumers import ws_connect, ws_message, ws_disconnect, TestPersistence


channel_routing = [
    route("websocket.connect", ws_connect, path=r"^/network_ui/test"),
    route("websocket.receive", ws_message, path=r"^/network_ui/test"),
    route("websocket.disconnect", ws_disconnect, path=r"^/network_ui/test"),
    route("test_persistence", TestPersistence().handle),
]


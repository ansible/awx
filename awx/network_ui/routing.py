# Copyright (c) 2017 Red Hat, Inc
from channels.routing import route
from awx.network_ui.consumers import ws_connect, ws_message, ws_disconnect, persistence

channel_routing = [
    route("websocket.connect", ws_connect, path=r"^/network_ui/topology"),
    route("websocket.receive", ws_message, path=r"^/network_ui/topology"),
    route("websocket.disconnect", ws_disconnect, path=r"^/network_ui/topology"),
    route("persistence", persistence.handle),
]

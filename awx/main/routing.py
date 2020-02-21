from django.conf.urls import url
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from . import consumers

websocket_urlpatterns = [
    url(r'websocket/$', consumers.EventConsumer),
    url(r'websocket/broadcast/$', consumers.BroadcastConsumer),
]

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})

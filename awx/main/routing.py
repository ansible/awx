from django.urls import re_path
from django.conf.urls import url
#from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from . import consumers

websocket_urlpatterns = [
    url(r'websocket/$', consumers.EventConsumer),
]

application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'websocket': URLRouter(
        websocket_urlpatterns
    ),
})

'''
application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'websocket': AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
'''

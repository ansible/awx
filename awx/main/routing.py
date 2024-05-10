import redis
import logging

from django.conf import settings
from django.urls import re_path

from channels.routing import ProtocolTypeRouter, URLRouter

from ansible_base.lib.channels.middleware import DrfAuthMiddlewareStack

from . import consumers


logger = logging.getLogger('awx.main.routing')
_application = None


class AWXProtocolTypeRouter(ProtocolTypeRouter):
    def __init__(self, *args, **kwargs):
        try:
            r = redis.Redis.from_url(settings.BROKER_URL)
            for k in r.scan_iter('asgi:*', 500):
                logger.debug(f"cleaning up Redis key {k}")
                r.delete(k)
        except redis.exceptions.RedisError as e:
            logger.warning("encountered an error communicating with redis.")
            raise e
        super().__init__(*args, **kwargs)


class MultipleURLRouterAdapter:
    """
    Django channels doesn't nicely support Auth_1(urls_1), Auth_2(urls_2), ..., Auth_n(urls_n)
    This class allows assocating a websocket url with an auth
    Ordering matters. The first matching url will be used.
    """

    def __init__(self, *auths):
        self._auths = [a for a in auths]

    async def __call__(self, scope, receive, send):
        """
        Loop through the list of passed in URLRouter's (they may or may not be wrapped by auth).
        We know we have exhausted the list of URLRouter patterns when we get a
        ValueError('No route found for path %s'). When that happens, move onto the next
        URLRouter.
        If the final URLRouter raises an error, re-raise it in the end.

        We know that we found a match when no error is raised, end the loop.
        """
        last_index = len(self._auths) - 1
        for i, auth in enumerate(self._auths):
            try:
                return await auth.__call__(scope, receive, send)
            except ValueError as e:
                if str(e).startswith('No route found for path'):
                    # Only surface the error if on the last URLRouter
                    if i == last_index:
                        raise


websocket_urlpatterns = [
    re_path(r'api/websocket/$', consumers.EventConsumer.as_asgi()),
    re_path(r'websocket/$', consumers.EventConsumer.as_asgi()),
]

if settings.OPTIONAL_API_URLPATTERN_PREFIX:
    websocket_urlpatterns.append(re_path(r'api/{}/v2/websocket/$'.format(settings.OPTIONAL_API_URLPATTERN_PREFIX), consumers.EventConsumer.as_asgi()))

websocket_relay_urlpatterns = [
    re_path(r'websocket/relay/$', consumers.RelayConsumer.as_asgi()),
]


def application_func(cls=AWXProtocolTypeRouter) -> ProtocolTypeRouter:
    return cls(
        {
            'websocket': MultipleURLRouterAdapter(
                URLRouter(websocket_relay_urlpatterns),
                DrfAuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
            )
        }
    )


def __getattr__(name: str) -> ProtocolTypeRouter:
    """
    Defer instantiating application.
    For testing, we just need it to NOT run on import.

    https://peps.python.org/pep-0562/#specification

    Normally, someone would get application from this module via:
        from awx.main.routing import application

    and do something with the application:
        application.do_something()

    What does the callstack look like when the import runs?
    ...
        awx.main.routing.__getattribute__(...)                              # <-- we don't define this so NOOP as far as we are concerned
        if '__getattr__' in awx.main.routing.__dict__:                      # <-- this triggers the function we are in
            return awx.main.routing.__dict__.__getattr__("application")

    Why isn't this function simply implemented as:
        def __getattr__(name):
            if not _application:
              _application = application_func()
            return _application

    It could. I manually tested it and it passes test_routing.py.

    But my understanding after reading the PEP-0562 specification link above is that
    performance would be a bit worse due to the extra __getattribute__ calls when
    we reference non-global variables.
    """
    if name == "application":
        globs = globals()
        if not globs['_application']:
            globs['_application'] = application_func()
        return globs['_application']
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

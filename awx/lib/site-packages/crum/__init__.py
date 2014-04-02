# Python
import contextlib
import logging
import threading

_thread_locals = threading.local()

_logger = logging.getLogger('crum')

__version__ = '0.6.1'

__all__ = ['get_current_request', 'get_current_user', 'impersonate']


@contextlib.contextmanager
def impersonate(user=None):
    """Temporarily impersonate the given user for audit trails."""
    try:
        current_user = get_current_user(_return_false=True)
        set_current_user(user)
        yield user
    finally:
        set_current_user(current_user)


def get_current_request():
    """Return the request associated with the current thread."""
    return getattr(_thread_locals, 'request', None)


def set_current_request(request=None):
    """Update the request associated with the current thread."""
    _thread_locals.request = request
    # Clear the current user if also clearing the request.
    if not request:
        set_current_user(False)


def get_current_user(_return_false=False):
    """Return the user associated with the current request thread."""
    from crum.signals import current_user_getter
    top_priority = -9999
    top_user = False if _return_false else None
    results = current_user_getter.send_robust(get_current_user)
    for receiver, response in results:
        priority = 0
        if isinstance(response, Exception):
            _logger.exception('%r raised exception: %s', receiver, response)
            continue
        elif isinstance(response, (tuple, list)) and response:
            user = response[0]
            if len(response) > 1:
                priority = response[1]
        elif response or response in (None, False):
            user = response
        else:
            _logger.error('%r returned invalid response: %r', receiver,
                          response)
            continue
        if user is not False:
            if priority > top_priority:
                top_priority = priority
                top_user = user
    return top_user


def set_current_user(user=None):
    """Update the user associated with the current request thread."""
    from crum.signals import current_user_setter
    results = current_user_setter.send_robust(set_current_user, user=user)
    for receiver, response in results:
        if isinstance(response, Exception):
            _logger.exception('%r raised exception: %s', receiver, response)


class CurrentRequestUserMiddleware(object):
    """Middleware to capture the request and user from the current thread."""

    def process_request(self, request):
        set_current_request(request)

    def process_response(self, request, response):
        set_current_request(None)
        return response

    def process_exception(self, request, exception):
        set_current_request(None)

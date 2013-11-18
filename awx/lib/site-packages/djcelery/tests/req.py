from __future__ import absolute_import, unicode_literals

from django.test import Client
from django.core.handlers.wsgi import WSGIRequest
from django.core.handlers.base import BaseHandler

from celery.utils.compat import WhateverIO


class RequestFactory(Client):
    """Class that lets you create mock Request objects for use in testing.

    Usage:

    rf = RequestFactory()
    get_request = rf.get('/hello/')
    post_request = rf.post('/submit/', {'foo': 'bar'})

    This class re-uses the django.test.client.Client interface, docs here:
    http://www.djangoproject.com/documentation/testing/#the-test-client

    Once you have a request object you can pass it to any view function,
    just as if that view had been hooked up using a URLconf.

    """

    def request(self, **request):
        """Similar to parent class, but returns the request object as
        soon as it has created it."""
        environ = {
            'HTTP_COOKIE': self.cookies,
            'HTTP_USER_AGENT': 'Django UnitTest Client 1.0',
            'REMOTE_ADDR': '127.0.0.1',
            'PATH_INFO': '/',
            'QUERY_STRING': '',
            'REQUEST_METHOD': 'GET',
            'SCRIPT_NAME': '',
            'SERVER_NAME': 'testserver',
            'SERVER_PORT': 80,
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'wsgi.input': WhateverIO(),
        }

        environ.update(self.defaults)
        environ.update(request)
        return WSGIRequest(environ)


class MockRequest(object):

    def __init__(self):
        handler = BaseHandler()
        handler.load_middleware()
        self.request_factory = RequestFactory()
        self.middleware = handler._request_middleware

    def _make_request(self, request_method, *args, **kwargs):
        request_method_handler = getattr(self.request_factory, request_method)
        request = request_method_handler(*args, **kwargs)
        [middleware_processor(request)
            for middleware_processor in self.middleware]
        return request

    def get(self, *args, **kwargs):
        return self._make_request('get', *args, **kwargs)

    def post(self, *args, **kwargs):
        return self._make_request('post', *args, **kwargs)

    def put(self, *args, **kwargs):
        return self._make_request('put', *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self._make_request('delete', *args, **kwargs)

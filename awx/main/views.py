# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Django
from django.shortcuts import render
from django.utils.html import format_html

# Django REST Framework
from rest_framework import exceptions, permissions, views


class ApiErrorView(views.APIView):

    authentication_classes = []
    permission_classes = (permissions.AllowAny,)
    metadata_class = None
    allowed_methods = ('GET', 'HEAD')
    exception_class = exceptions.APIException
    view_name = 'API Error'

    def get_view_name(self):
        return self.view_name

    def get(self, request, format=None):
        raise self.exception_class()


def handle_error(request, status=404, **kwargs):
    # For errors to /api/*, use a simple DRF view/exception to generate a
    # browsable error page for browser clients or a simple JSON response for any
    # other clients.
    if request.path.startswith('/api/'):
        class APIException(exceptions.APIException):
            status_code = status
            default_detail = kwargs['content']
        api_error_view = ApiErrorView.as_view(view_name=kwargs['name'], exception_class=APIException)
        return api_error_view(request)
    else:
        kwargs['content'] = format_html('<span class="nocode">{}</span>', kwargs.get('content', ''))
        return render(request, 'error.html', kwargs, status=status)


def handle_400(request):
    kwargs = {
        'name': 'Bad Request',
        'content': 'The request could not be understood by the server.',
    }
    return handle_error(request, 400, **kwargs)


def handle_403(request):
    kwargs = {
        'name': 'Forbidden',
        'content': 'You don\'t have permission to access the requested resource.',
    }
    return handle_error(request, 403, **kwargs)


def handle_404(request):
    kwargs = {
        'name': 'Not Found',
        'content': 'The requested resource could not be found.',
    }
    return handle_error(request, 404, **kwargs)


def handle_500(request):
    kwargs = {
        'name': 'Server Error',
        'content': 'A server error has occurred.',
    }
    return handle_error(request, 500, **kwargs)

# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

import json

# Django
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt

# Django REST Framework
from rest_framework import exceptions, permissions, views

import logging


def _force_raising_exception(view_obj, request, format=None):
    raise view_obj.exception_class()


class ApiErrorView(views.APIView):

    authentication_classes = []
    permission_classes = (permissions.AllowAny,)
    metadata_class = None
    exception_class = exceptions.APIException

    name = _('API Error')

    def finalize_response(self, request, response, *args, **kwargs):
        response = super(ApiErrorView, self).finalize_response(request, response, *args, **kwargs)
        try:
            del response['Allow']
        except Exception:
            pass
        return response


for method_name in ApiErrorView.http_method_names:
    setattr(ApiErrorView, method_name, _force_raising_exception)


def handle_error(request, status=404, **kwargs):
    # For errors to /api/*, use a simple DRF view/exception to generate a
    # browsable error page for browser clients or a simple JSON response for any
    # other clients.
    if request.path.startswith('/api/'):
        class APIException(exceptions.APIException):
            status_code = status
            default_detail = kwargs['content']
        api_error_view = ApiErrorView.as_view(exception_class=APIException)
        response = api_error_view(request)
        if hasattr(response, 'render'):
            response.render()
        return response
    else:
        kwargs['content'] = format_html('<span class="nocode">{}</span>', kwargs.get('content', ''))
        return render(request, 'error.html', kwargs, status=status)


def handle_400(request, exception):
    kwargs = {
        'name': _('Bad Request'),
        'content': _('The request could not be understood by the server.'),
    }
    return handle_error(request, 400, **kwargs)


def handle_403(request, exception):
    kwargs = {
        'name': _('Forbidden'),
        'content': _('You don\'t have permission to access the requested resource.'),
    }
    return handle_error(request, 403, **kwargs)


def handle_404(request, exception):
    kwargs = {
        'name': _('Not Found'),
        'content': _('The requested resource could not be found.'),
    }
    return handle_error(request, 404, **kwargs)


def handle_500(request):
    kwargs = {
        'name': _('Server Error'),
        'content': _('A server error has occurred.'),
    }
    return handle_error(request, 500, **kwargs)


@csrf_exempt
def handle_csp_violation(request):
    logger = logging.getLogger('awx')
    logger.error(json.loads(request.body))
    return HttpResponse(content=None)


def handle_login_redirect(request):
    return HttpResponseRedirect("/#/login")

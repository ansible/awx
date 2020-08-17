# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

from django.utils.safestring import SafeText
from prometheus_client.parser import text_string_to_metric_families

# Django REST Framework
from rest_framework import renderers
from rest_framework.request import override_method
from rest_framework.utils import encoders


class SurrogateEncoder(encoders.JSONEncoder):

    def encode(self, obj):
        ret = super(SurrogateEncoder, self).encode(obj)
        try:
            ret.encode()
        except UnicodeEncodeError as e:
            if 'surrogates not allowed' in e.reason:
                ret = ret.encode('utf-8', 'replace').decode()
        return ret


class DefaultJSONRenderer(renderers.JSONRenderer):

    encoder_class = SurrogateEncoder


class BrowsableAPIRenderer(renderers.BrowsableAPIRenderer):
    '''
    Customizations to the default browsable API renderer.
    '''

    def get_default_renderer(self, view):
        renderer = super(BrowsableAPIRenderer, self).get_default_renderer(view)
        # Always use JSON renderer for browsable OPTIONS response.
        if view.request.method == 'OPTIONS' and not isinstance(renderer, renderers.JSONRenderer):
            return renderers.JSONRenderer()
        return renderer

    def get_content(self, renderer, data, accepted_media_type, renderer_context):
        if isinstance(data, SafeText):
            # Older versions of Django (pre-2.0) have a py3 bug which causes
            # bytestrings marked as "safe" to not actually get _treated_ as
            # safe; this causes certain embedded strings (like the stdout HTML
            # view) to be improperly escaped
            # see: https://github.com/ansible/awx/issues/3108
            # https://code.djangoproject.com/ticket/28121
            return data
        return super(BrowsableAPIRenderer, self).get_content(renderer, data,
                                                             accepted_media_type,
                                                             renderer_context)

    def get_context(self, data, accepted_media_type, renderer_context):
        # Store the associated response status to know how to populate the raw
        # data form.
        try:
            setattr(renderer_context['view'], '_raw_data_response_status', renderer_context['response'].status_code)
            setattr(renderer_context['view'], '_request', renderer_context['request'])
            return super(BrowsableAPIRenderer, self).get_context(data, accepted_media_type, renderer_context)
        finally:
            delattr(renderer_context['view'], '_raw_data_response_status')
            delattr(renderer_context['view'], '_request')

    def get_raw_data_form(self, data, view, method, request):
        # Set a flag on the view to indiciate to the view/serializer that we're
        # creating a raw data form for the browsable API.  Store the original
        # request method to determine how to populate the raw data form.
        if request.method in {'OPTIONS', 'DELETE'}:
            return
        try:
            setattr(view, '_raw_data_form_marker', True)
            setattr(view, '_raw_data_request_method', request.method)
            return super(BrowsableAPIRenderer, self).get_raw_data_form(data, view, method, request)
        finally:
            delattr(view, '_raw_data_form_marker')
            delattr(view, '_raw_data_request_method')

    def get_rendered_html_form(self, data, view, method, request):
        # Never show auto-generated form (only raw form).
        obj = getattr(view, 'object', None)
        if obj is None and hasattr(view, 'get_object') and hasattr(view, 'retrieve'):
            try:
                view.object = view.get_object()
                obj = view.object
            except Exception:
                obj = None
        with override_method(view, request, method) as request:
            if not self.show_form_for_method(view, method, request, obj):
                return
            if method in ('DELETE', 'OPTIONS'):
                return True  # Don't actually need to return a form

    def get_filter_form(self, data, view, request):
        # Don't show filter form in browsable API.
        return


class PlainTextRenderer(renderers.BaseRenderer):

    media_type = 'text/plain'
    format = 'txt'

    def render(self, data, media_type=None, renderer_context=None):
        if not isinstance(data, str):
            data = str(data)
        return data.encode(self.charset)


class DownloadTextRenderer(PlainTextRenderer):

    format = "txt_download"


class AnsiTextRenderer(PlainTextRenderer):

    media_type = 'text/plain'
    format = 'ansi'


class AnsiDownloadRenderer(PlainTextRenderer):

    format = "ansi_download"


class PrometheusJSONRenderer(renderers.JSONRenderer):

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if isinstance(data, dict):
            # HTTP errors are {'detail': ErrorDetail(string='...', code=...)}
            return super(PrometheusJSONRenderer, self).render(
                data, accepted_media_type, renderer_context
            )
        parsed_metrics = text_string_to_metric_families(data)
        data = {}
        for family in parsed_metrics:
            for sample in family.samples:
                data[sample[0]] = {"labels": sample[1], "value": sample[2]}
        return super(PrometheusJSONRenderer, self).render(
            data, accepted_media_type, renderer_context
        )

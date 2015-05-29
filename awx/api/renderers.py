# Copyright (c) 2015 Ansible, Inc. (formerly AnsibleWorks, Inc.)
# All Rights Reserved.

# Django REST Framework
from rest_framework import renderers

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

    def get_raw_data_form(self, view, method, request):
        try:
            setattr(view, '_raw_data_form_marker', True)
            return super(BrowsableAPIRenderer, self).get_raw_data_form(view, method, request)
        finally:
            delattr(view, '_raw_data_form_marker')

    def get_rendered_html_form(self, view, method, request):
        '''Never show auto-generated form (only raw form).'''
        obj = getattr(view, 'object', None)
        if not self.show_form_for_method(view, method, request, obj):
            return
        if method in ('DELETE', 'OPTIONS'):
            return True  # Don't actually need to return a form

    def get_context(self, data, accepted_media_type, renderer_context):
        context = super(BrowsableAPIRenderer, self).get_context(data, accepted_media_type, renderer_context)
        return context

class PlainTextRenderer(renderers.BaseRenderer):

    media_type = 'text/plain'
    format = 'txt'

    def render(self, data, media_type=None, renderer_context=None):
        if not isinstance(data, basestring):
            data = unicode(data)
        return data.encode(self.charset)

class AnsiTextRenderer(PlainTextRenderer):

    media_type = 'text/plain'
    format = 'ansi'

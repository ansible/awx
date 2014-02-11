# Copyright (c) 2014 AnsibleWorks, Inc.
# All Rights Reserved.

# Django
from django.conf import settings
from django.shortcuts import render
from django.template import RequestContext
from django.utils.safestring import mark_safe

def handle_error(request, status=404, **kwargs):
    # FIXME: Should attempt to check HTTP Accept request header and return
    # plain JSON response instead of HTML (maybe only for /api/*).
    context = kwargs
    if 'django.contrib.admin' in settings.INSTALLED_APPS and request.path.startswith('/admin/'):
        template_name = 'admin/error.html'
    else:
        # Return enough context to popuplate the base API template.
        description = u'<pre class="err">%s</pre>' % context.get('content', '')
        context['description'] = mark_safe(description)
        context['content'] = ''
        template_name = 'error.html'
    return render(request, template_name, context, status=status)

def handle_403(request):
    kwargs = {
        'name': 'Forbidden',
        'content': 'You don\'t have permission to access the requested page.',
    }
    return handle_error(request, 403, **kwargs)

def handle_404(request):
    kwargs = {
        'name': 'Not Found',
        'content': 'The requested page could not be found.',
    }
    return handle_error(request, 404, **kwargs)

def handle_500(request):
    kwargs = {
        'name': 'Server Error',
        'content': 'A server error has occurred.',
    }
    return handle_error(request, 500, **kwargs)

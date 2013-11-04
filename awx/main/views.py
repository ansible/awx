# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

# Django
from django.shortcuts import render_to_response
from django.template import RequestContext

def handle_error(request, status=404):
    context = {}
    #print request.path, status
    if request.path.startswith('/admin/'):
        template_name = 'admin/%d.html' % status
    else:
        template_name = '%d.html' % status
    return render_to_response(template_name, context,
                              context_instance=RequestContext(request))

def handle_403(request):
    return handle_error(request, 403)

def handle_404(request):
    return handle_error(request, 404)

def handle_500(request):
    return handle_error(request, 500)

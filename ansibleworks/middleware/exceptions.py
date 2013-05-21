# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

import traceback
from django.http import HttpResponse

class ExceptionMiddleware(object):

    def process_exception(self, request, exception):
        # FIXME: Should only format plain text for API exceptions.
        return HttpResponse(traceback.format_exc(exception), content_type="text/plain", status=500)


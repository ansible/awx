# Copyright (c) 2013 AnsibleWorks, Inc.
# All Rights Reserved.

import traceback
from django.http import HttpResponse

class ExceptionMiddleware(object):

    def process_exception(self, request, exception):
        if request.path.startswith('/api/'):
            # FIXME: For GA, we shouldn't provide this level of detail to the
            # end user.
            return HttpResponse(traceback.format_exc(exception), content_type="text/plain", status=500)

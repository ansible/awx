import traceback
from django.http import HttpResponse

class ExceptionMiddleware(object):

    def process_exception(self, request, exception):
        return HttpResponse(traceback.format_exc(exception), content_type="text/plain", status=500)


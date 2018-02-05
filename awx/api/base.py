from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from rest_framework.settings import api_settings
from rest_framework_yaml.parsers import YAMLParser
from rest_framework_yaml.renderers import YAMLRenderer

from awx.api.generics import (
    SubListCreateAttachDetachAPIView,
    RetrieveUpdateAPIView,
    SubListAPIView,
)
from awx.api.serializers import (
    AdHocCommandEventSerializer,
    JobHostSummarySerializer,
    JobEventSerializer,
)
from awx.main.models import (
    AdHocCommandEvent,
    User,
    JobEvent,
    JobHostSummary,
)


class BaseUsersList(SubListCreateAttachDetachAPIView):
    def post(self, request, *args, **kwargs):
        ret = super(BaseUsersList, self).post( request, *args, **kwargs)
        try:
            if ret.data is not None and request.data.get('is_system_auditor', False):
                # This is a faux-field that just maps to checking the system
                # auditor role member list.. unfortunately this means we can't
                # set it on creation, and thus needs to be set here.
                user = User.objects.get(id=ret.data['id'])
                user.is_system_auditor = request.data['is_system_auditor']
                ret.data['is_system_auditor'] = request.data['is_system_auditor']
        except AttributeError as exc:
            print(exc)
            pass
        return ret
 

class BaseVariableData(RetrieveUpdateAPIView):

    parser_classes = api_settings.DEFAULT_PARSER_CLASSES + [YAMLParser]
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES + [YAMLRenderer]
    is_variable_data = True # Special flag for permissions check.


class BaseJobHostSummariesList(SubListAPIView):

    model = JobHostSummary
    serializer_class = JobHostSummarySerializer
    parent_model = None # Subclasses must define this attribute.
    relationship = 'job_host_summaries'
    view_name = _('Job Host Summaries List')

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        return getattr(parent, self.relationship).select_related('job', 'job__job_template', 'host')


class BaseJobEventsList(SubListAPIView):

    model = JobEvent
    serializer_class = JobEventSerializer
    parent_model = None # Subclasses must define this attribute.
    relationship = 'job_events'
    view_name = _('Job Events List')
    search_fields = ('stdout',)

    def finalize_response(self, request, response, *args, **kwargs):
        response['X-UI-Max-Events'] = settings.RECOMMENDED_MAX_EVENTS_DISPLAY_HEADER
        return super(BaseJobEventsList, self).finalize_response(request, response, *args, **kwargs)


class BaseAdHocCommandEventsList(SubListAPIView):

    model = AdHocCommandEvent
    serializer_class = AdHocCommandEventSerializer
    parent_model = None # Subclasses must define this attribute.
    relationship = 'ad_hoc_command_events'
    view_name = _('Ad Hoc Command Events List')
    new_in_220 = True

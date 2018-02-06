# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

import cgi
import logging
import os
import re
import subprocess
from base64 import b64encode

from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.db import transaction, connection
from django.http import HttpResponse
from django.template.loader import render_to_string

from rest_framework.response import Response
from rest_framework import status
from rest_framework.settings import api_settings

import ansiconv

from wsgiref.util import FileWrapper

from awx.api.generics import (
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    SubListAPIView,
    GenericAPIView,
    RetrieveAPIView,
    get_view_name,
)
from awx.api.base import (
    BaseJobHostSummariesList,
    BaseJobEventsList,
)
from awx.main.models import (
    ActivityStream,
    AdHocCommand,
    Job,
    JobHostSummary,
    Host,
    JobEvent,
    Notification,
    Label,
)
from awx.api.metadata import JobTypeMetadata
from awx.api.serializers import (
    HostSerializer,
    EmptySerializer,
    JobEventSerializer,
    JobCancelSerializer,
    LabelSerializer,
    NotificationSerializer,
    ActivityStreamSerializer,
    JobListSerializer,
    JobHostSummarySerializer,
    JobRelaunchSerializer,
    JobSerializer,
    UnifiedJobStdoutSerializer,
)
from awx.api.renderers import (
    BrowsableAPIRenderer,
    StaticHTMLRenderer,
    PlainTextRenderer,
    AnsiTextRenderer,
    JSONRenderer,
    DownloadTextRenderer,
    AnsiDownloadRenderer,
)
from awx.api.views.mixins import (
    UnifiedJobDeletionMixin,
    ActivityStreamEnforcementMixin,
)
from awx.api.authentication import TokenGetAuthentication
from awx.api.versioning import get_request_version
from awx.main.models.unified_jobs import ACTIVE_STATES

logger = logging.getLogger('awx.api.views')


class JobList(ListCreateAPIView):

    model = Job
    metadata_class = JobTypeMetadata
    serializer_class = JobListSerializer

    @property
    def allowed_methods(self):
        methods = super(JobList, self).allowed_methods
        if get_request_version(self.request) > 1:
            methods.remove('POST')
        return methods

    # NOTE: Remove in 3.3, switch ListCreateAPIView to ListAPIView
    def post(self, request, *args, **kwargs):
        if get_request_version(self.request) > 1:
            return Response({"error": _("POST not allowed for Job launching in version 2 of the api")},
                            status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super(JobList, self).post(request, *args, **kwargs)


class JobDetail(UnifiedJobDeletionMixin, RetrieveUpdateDestroyAPIView):

    model = Job
    metadata_class = JobTypeMetadata
    serializer_class = JobSerializer

    def update(self, request, *args, **kwargs):
        obj = self.get_object()
        # Only allow changes (PUT/PATCH) when job status is "new".
        if obj.status != 'new':
            return self.http_method_not_allowed(request, *args, **kwargs)
        return super(JobDetail, self).update(request, *args, **kwargs)


class JobLabelList(SubListAPIView):

    model = Label
    serializer_class = LabelSerializer
    parent_model = Job
    relationship = 'labels'
    parent_key = 'job'
    new_in_300 = True


class JobActivityStreamList(ActivityStreamEnforcementMixin, SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = Job
    relationship = 'activitystream_set'
    new_in_145 = True


# TODO: remove endpoint in 3.3
class JobStart(GenericAPIView):

    model = Job
    obj_permission_type = 'start'
    serializer_class = EmptySerializer
    deprecated = True

    def v2_not_allowed(self):
        return Response({'detail': 'Action only possible through v1 API.'},
                        status=status.HTTP_404_NOT_FOUND)

    def get(self, request, *args, **kwargs):
        if get_request_version(request) > 1:
            return self.v2_not_allowed()
        obj = self.get_object()
        data = dict(
            can_start=obj.can_start,
        )
        if obj.can_start:
            data['passwords_needed_to_start'] = obj.passwords_needed_to_start
            data['ask_variables_on_launch'] = obj.ask_variables_on_launch
        return Response(data)

    def post(self, request, *args, **kwargs):
        if get_request_version(request) > 1:
            return self.v2_not_allowed()
        obj = self.get_object()
        if obj.can_start:
            result = obj.signal_start(**request.data)
            if not result:
                data = dict(passwords_needed_to_start=obj.passwords_needed_to_start)
                return Response(data, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)


class JobCancel(RetrieveAPIView):

    model = Job
    obj_permission_type = 'cancel'
    serializer_class = JobCancelSerializer

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.can_cancel:
            obj.cancel()
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)


class JobRelaunch(RetrieveAPIView):

    model = Job
    obj_permission_type = 'start'
    serializer_class = JobRelaunchSerializer

    @csrf_exempt
    @transaction.non_atomic_requests
    def dispatch(self, *args, **kwargs):
        return super(JobRelaunch, self).dispatch(*args, **kwargs)

    def check_object_permissions(self, request, obj):
        if request.method == 'POST' and obj:
            relaunch_perm, messages = request.user.can_access_with_errors(self.model, 'start', obj)
            if not relaunch_perm and 'detail' in messages:
                self.permission_denied(request, message=messages['detail'])
        return super(JobRelaunch, self).check_object_permissions(request, obj)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()

        # Note: is_valid() may modify request.data
        # It will remove any key/value pair who's key is not in the 'passwords_needed_to_start' list
        serializer = self.serializer_class(data=request.data, context={'obj': obj, 'data': request.data})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        copy_kwargs = {}
        retry_hosts = request.data.get('hosts', None)
        if retry_hosts and retry_hosts != 'all':
            if obj.status in ACTIVE_STATES:
                return Response({'hosts': _(
                    'Wait until job finishes before retrying on {status_value} hosts.'
                ).format(status_value=retry_hosts)}, status=status.HTTP_400_BAD_REQUEST)
            host_qs = obj.retry_qs(retry_hosts)
            if not obj.job_events.filter(event='playbook_on_stats').exists():
                return Response({'hosts': _(
                    'Cannot retry on {status_value} hosts, playbook stats not available.'
                ).format(status_value=retry_hosts)}, status=status.HTTP_400_BAD_REQUEST)
            retry_host_list = host_qs.values_list('name', flat=True)
            if len(retry_host_list) == 0:
                return Response({'hosts': _(
                    'Cannot relaunch because previous job had 0 {status_value} hosts.'
                ).format(status_value=retry_hosts)}, status=status.HTTP_400_BAD_REQUEST)
            copy_kwargs['limit'] = ','.join(retry_host_list)

        new_job = obj.copy_unified_job(**copy_kwargs)
        result = new_job.signal_start(**request.data)
        if not result:
            data = dict(passwords_needed_to_start=new_job.passwords_needed_to_start)
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        else:
            data = JobSerializer(new_job, context=self.get_serializer_context()).data
            # Add job key to match what old relaunch returned.
            data['job'] = new_job.id
            headers = {'Location': new_job.get_absolute_url(request=request)}
            return Response(data, status=status.HTTP_201_CREATED, headers=headers)


class JobNotificationsList(SubListAPIView):

    model = Notification
    serializer_class = NotificationSerializer
    parent_model = Job
    relationship = 'notifications'
    new_in_300 = True


class JobJobHostSummariesList(BaseJobHostSummariesList):

    parent_model = Job


class JobHostSummaryDetail(RetrieveAPIView):

    model = JobHostSummary
    serializer_class = JobHostSummarySerializer


class JobEventList(ListAPIView):

    model = JobEvent
    serializer_class = JobEventSerializer


class JobEventDetail(RetrieveAPIView):

    model = JobEvent
    serializer_class = JobEventSerializer


class JobEventChildrenList(SubListAPIView):

    model = JobEvent
    serializer_class = JobEventSerializer
    parent_model = JobEvent
    relationship = 'children'
    view_name = _('Job Event Children List')


class JobEventHostsList(SubListAPIView):

    model = Host
    serializer_class = HostSerializer
    parent_model = JobEvent
    relationship = 'hosts'
    view_name = _('Job Event Hosts List')
    capabilities_prefetch = ['inventory.admin']


class JobJobEventsList(BaseJobEventsList):

    parent_model = Job

    def get_queryset(self):
        job = self.get_parent_object()
        self.check_parent_access(job)
        qs = job.job_events
        qs = qs.select_related('host')
        qs = qs.prefetch_related('hosts', 'children')
        return qs.all()


class StdoutANSIFilter(object):

    def __init__(self, fileobj):
        self.fileobj = fileobj
        self.extra_data = ''
        if hasattr(fileobj,'close'):
            self.close = fileobj.close

    def read(self, size=-1):
        data = self.extra_data
        while size > 0 and len(data) < size:
            line = self.fileobj.readline(size)
            if not line:
                break
            # Remove ANSI escape sequences used to embed event data.
            line = re.sub(r'\x1b\[K(?:[A-Za-z0-9+/=]+\x1b\[\d+D)+\x1b\[K', '', line)
            # Remove ANSI color escape sequences.
            line = re.sub(r'\x1b[^m]*m', '', line)
            data += line
        if size > 0 and len(data) > size:
            self.extra_data = data[size:]
            data = data[:size]
        else:
            self.extra_data = ''
        return data


class UnifiedJobStdout(RetrieveAPIView):

    authentication_classes = [TokenGetAuthentication] + api_settings.DEFAULT_AUTHENTICATION_CLASSES
    serializer_class = UnifiedJobStdoutSerializer
    renderer_classes = [BrowsableAPIRenderer, StaticHTMLRenderer,
                        PlainTextRenderer, AnsiTextRenderer,
                        JSONRenderer, DownloadTextRenderer, AnsiDownloadRenderer]
    filter_backends = ()
    new_in_148 = True

    def retrieve(self, request, *args, **kwargs):
        unified_job = self.get_object()
        obj_size = unified_job.result_stdout_size
        if request.accepted_renderer.format not in {'txt_download', 'ansi_download'} and obj_size > settings.STDOUT_MAX_BYTES_DISPLAY:
            response_message = _("Standard Output too large to display (%(text_size)d bytes), "
                                 "only download supported for sizes over %(supported_size)d bytes") % {
                'text_size': obj_size, 'supported_size': settings.STDOUT_MAX_BYTES_DISPLAY}
            if request.accepted_renderer.format == 'json':
                return Response({'range': {'start': 0, 'end': 1, 'absolute_end': 1}, 'content': response_message})
            else:
                return Response(response_message)

        if request.accepted_renderer.format in ('html', 'api', 'json'):
            content_format = request.query_params.get('content_format', 'html')
            content_encoding = request.query_params.get('content_encoding', None)
            start_line = request.query_params.get('start_line', 0)
            end_line = request.query_params.get('end_line', None)
            dark_val = request.query_params.get('dark', '')
            dark = bool(dark_val and dark_val[0].lower() in ('1', 't', 'y'))
            content_only = bool(request.accepted_renderer.format in ('api', 'json'))
            dark_bg = (content_only and dark) or (not content_only and (dark or not dark_val))
            content, start, end, absolute_end = unified_job.result_stdout_raw_limited(start_line, end_line)

            # Remove any ANSI escape sequences containing job event data.
            content = re.sub(r'\x1b\[K(?:[A-Za-z0-9+/=]+\x1b\[\d+D)+\x1b\[K', '', content)

            body = ansiconv.to_html(cgi.escape(content))

            context = {
                'title': get_view_name(self.__class__),
                'body': mark_safe(body),
                'dark': dark_bg,
                'content_only': content_only,
            }
            data = render_to_string('api/stdout.html', context).strip()

            if request.accepted_renderer.format == 'api':
                return Response(mark_safe(data))
            if request.accepted_renderer.format == 'json':
                if content_encoding == 'base64' and content_format == 'ansi':
                    return Response({'range': {'start': start, 'end': end, 'absolute_end': absolute_end}, 'content': b64encode(content)})
                elif content_format == 'html':
                    return Response({'range': {'start': start, 'end': end, 'absolute_end': absolute_end}, 'content': body})
            return Response(data)
        elif request.accepted_renderer.format == 'txt':
            return Response(unified_job.result_stdout)
        elif request.accepted_renderer.format == 'ansi':
            return Response(unified_job.result_stdout_raw)
        elif request.accepted_renderer.format in {'txt_download', 'ansi_download'}:
            if not os.path.exists(unified_job.result_stdout_file):
                write_fd = open(unified_job.result_stdout_file, 'w')
                with connection.cursor() as cursor:
                    try:
                        tablename, related_name = {
                            Job: ('main_jobevent', 'job_id'),
                            AdHocCommand: ('main_adhoccommandevent', 'ad_hoc_command_id'),
                        }.get(unified_job.__class__, (None, None))
                        if tablename is None:
                            # stdout job event reconstruction isn't supported
                            # for certain job types (such as inventory syncs),
                            # so just grab the raw stdout from the DB
                            write_fd.write(unified_job.result_stdout_text)
                            write_fd.close()
                        else:
                            cursor.copy_expert(
                                "copy (select stdout from {} where {}={} order by start_line) to stdout".format(
                                    tablename,
                                    related_name,
                                    unified_job.id
                                ),
                                write_fd
                            )
                            write_fd.close()
                            subprocess.Popen("sed -i 's/\\\\r\\\\n/\\n/g' {}".format(unified_job.result_stdout_file),
                                             shell=True).wait()
                    except Exception as e:
                        return Response({"error": _("Error generating stdout download file: {}".format(e))})
            try:
                content_fd = open(unified_job.result_stdout_file, 'r')
                if request.accepted_renderer.format == 'txt_download':
                    # For txt downloads, filter out ANSI escape sequences.
                    content_fd = StdoutANSIFilter(content_fd)
                    suffix = ''
                else:
                    suffix = '_ansi'
                response = HttpResponse(FileWrapper(content_fd), content_type='text/plain')
                response["Content-Disposition"] = 'attachment; filename="job_%s%s.txt"' % (str(unified_job.id), suffix)
                return response
            except Exception as e:
                return Response({"error": _("Error generating stdout download file: %s") % str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return super(UnifiedJobStdout, self).retrieve(request, *args, **kwargs)


class JobStdout(UnifiedJobStdout):

    model = Job


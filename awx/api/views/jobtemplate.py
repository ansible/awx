# Copyright (c) 2018 Ansible, Inc.
# All Rights Reserved.

# Python
import time
import socket
from collections import OrderedDict, Iterable
import six


# Django
from django.conf import settings
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _


# Django REST Framework
from rest_framework.exceptions import PermissionDenied, ParseError
from rest_framework.parsers import FormParser
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework import status

# AWX
from awx.main.utils import getattrd
from awx.api.versioning import get_request_version
from awx.conf.license import feature_enabled, LicenseForbids
from awx.main.utils import extract_ansible_vars
from awx.main.utils.encryption import encrypt_value
from awx.api.permissions import JobTemplateCallbackPermission
from awx.api.metadata import JobTypeMetadata
from awx.main.models import (
    ActivityStream,
    Credential,
    NotificationTemplate,
    Role,
    User,
    JobTemplate,
    JobLaunchConfig,
    Job,
    Schedule,
    WorkflowJob,
    InstanceGroup,
    InventoryUpdate,
)
from awx.api.generics import (
    RetrieveAPIView,
    GenericAPIView,
    SubListCreateAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    SubListAPIView,
    SubListCreateAttachDetachAPIView,
    ResourceAccessList,
    CopyAPIView,
    SubListAttachDetachAPIView,
)
from awx.api.serializers import (
    ActivityStreamSerializer,
    RoleSerializer,
    NotificationTemplateSerializer,
    CredentialSerializer,
    JobTemplateSerializer,
    EmptySerializer,
    ScheduleSerializer,
    JobLaunchSerializer,
    WorkflowJobSerializer,
    WorkflowJobListSerializer,
    JobSerializer,
    JobListSerializer,
    InstanceGroupSerializer,
)
from awx.api.views.mixin import (
    ActivityStreamEnforcementMixin,
    RelatedJobsPreventDeleteMixin,
)


class JobTemplateList(ListCreateAPIView):

    model = JobTemplate
    metadata_class = JobTypeMetadata
    serializer_class = JobTemplateSerializer
    always_allow_superuser = False

    def post(self, request, *args, **kwargs):
        ret = super(JobTemplateList, self).post(request, *args, **kwargs)
        if ret.status_code == 201:
            job_template = JobTemplate.objects.get(id=ret.data['id'])
            job_template.admin_role.members.add(request.user)
        return ret


class JobTemplateDetail(RelatedJobsPreventDeleteMixin, RetrieveUpdateDestroyAPIView):

    model = JobTemplate
    metadata_class = JobTypeMetadata
    serializer_class = JobTemplateSerializer
    always_allow_superuser = False


class JobTemplateLaunch(RetrieveAPIView):

    model = JobTemplate
    obj_permission_type = 'start'
    metadata_class = JobTypeMetadata
    serializer_class = JobLaunchSerializer
    always_allow_superuser = False

    def update_raw_data(self, data):
        try:
            obj = self.get_object()
        except PermissionDenied:
            return data
        extra_vars = data.pop('extra_vars', None) or {}
        if obj:
            needed_passwords = obj.passwords_needed_to_start
            if needed_passwords:
                data['credential_passwords'] = {}
                for p in needed_passwords:
                    data['credential_passwords'][p] = u''
            else:
                data.pop('credential_passwords')
            for v in obj.variables_needed_to_start:
                extra_vars.setdefault(v, u'')
            if extra_vars:
                data['extra_vars'] = extra_vars
            modified_ask_mapping = JobTemplate.get_ask_mapping()
            modified_ask_mapping.pop('extra_vars')
            for field, ask_field_name in modified_ask_mapping.items():
                if not getattr(obj, ask_field_name):
                    data.pop(field, None)
                elif field == 'inventory':
                    data[field] = getattrd(obj, "%s.%s" % (field, 'id'), None)
                elif field == 'credentials':
                    data[field] = [cred.id for cred in obj.credentials.all()]
                else:
                    data[field] = getattr(obj, field)
        return data

    def modernize_launch_payload(self, data, obj):
        '''
        Steps to do simple translations of request data to support
        old field structure to launch endpoint
        TODO: delete this method with future API version changes
        '''
        ignored_fields = {}
        modern_data = data.copy()

        for fd in ('credential', 'vault_credential', 'inventory'):
            id_fd = '{}_id'.format(fd)
            if fd not in modern_data and id_fd in modern_data:
                modern_data[fd] = modern_data[id_fd]

        # This block causes `extra_credentials` to _always_ raise error if
        # the launch endpoint if we're accessing `/api/v1/`
        if get_request_version(self.request) == 1 and 'extra_credentials' in modern_data:
            raise ParseError({"extra_credentials": _(
                "Field is not allowed for use with v1 API."
            )})

        # Automatically convert legacy launch credential arguments into a list of `.credentials`
        if 'credentials' in modern_data and (
            'credential' in modern_data or
            'vault_credential' in modern_data or
            'extra_credentials' in modern_data
        ):
            raise ParseError({"error": _(
                "'credentials' cannot be used in combination with 'credential', 'vault_credential', or 'extra_credentials'."
            )})

        if (
            'credential' in modern_data or
            'vault_credential' in modern_data or
            'extra_credentials' in modern_data
        ):
            # make a list of the current credentials
            existing_credentials = obj.credentials.all()
            template_credentials = list(existing_credentials)  # save copy of existing
            new_credentials = []
            for key, conditional, _type, type_repr in (
                ('credential', lambda cred: cred.credential_type.kind != 'ssh', int, 'pk value'),
                ('vault_credential', lambda cred: cred.credential_type.kind != 'vault', int, 'pk value'),
                ('extra_credentials', lambda cred: cred.credential_type.kind not in ('cloud', 'net'), Iterable, 'a list')
            ):
                if key in modern_data:
                    # if a specific deprecated key is specified, remove all
                    # credentials of _that_ type from the list of current
                    # credentials
                    existing_credentials = filter(conditional, existing_credentials)
                    prompted_value = modern_data.pop(key)

                    # validate type, since these are not covered by a serializer
                    if not isinstance(prompted_value, _type):
                        msg = _(
                            "Incorrect type. Expected {}, received {}."
                        ).format(type_repr, prompted_value.__class__.__name__)
                        raise ParseError({key: [msg], 'credentials': [msg]})

                    # add the deprecated credential specified in the request
                    if not isinstance(prompted_value, Iterable) or isinstance(prompted_value, basestring):
                        prompted_value = [prompted_value]

                    # If user gave extra_credentials, special case to use exactly
                    # the given list without merging with JT credentials
                    if key == 'extra_credentials' and prompted_value:
                        obj._deprecated_credential_launch = True  # signal to not merge credentials
                    new_credentials.extend(prompted_value)

            # combine the list of "new" and the filtered list of "old"
            new_credentials.extend([cred.pk for cred in existing_credentials])
            if new_credentials:
                # If provided list doesn't contain the pre-existing credentials
                # defined on the template, add them back here
                for cred_obj in template_credentials:
                    if cred_obj.pk not in new_credentials:
                        new_credentials.append(cred_obj.pk)
                modern_data['credentials'] = new_credentials

        # credential passwords were historically provided as top-level attributes
        if 'credential_passwords' not in modern_data:
            modern_data['credential_passwords'] = data.copy()

        return (modern_data, ignored_fields)


    def post(self, request, *args, **kwargs):
        obj = self.get_object()

        try:
            modern_data, ignored_fields = self.modernize_launch_payload(
                data=request.data, obj=obj
            )
        except ParseError as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.serializer_class(data=modern_data, context={'template': obj})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        ignored_fields.update(serializer._ignored_fields)

        if not request.user.can_access(JobLaunchConfig, 'add', serializer.validated_data, template=obj):
            raise PermissionDenied()

        passwords = serializer.validated_data.pop('credential_passwords', {})
        new_job = obj.create_unified_job(**serializer.validated_data)
        result = new_job.signal_start(**passwords)

        if not result:
            data = dict(passwords_needed_to_start=new_job.passwords_needed_to_start)
            new_job.delete()
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        else:
            data = OrderedDict()
            if isinstance(new_job, WorkflowJob):
                data['workflow_job'] = new_job.id
                data['ignored_fields'] = self.sanitize_for_response(ignored_fields)
                data.update(WorkflowJobSerializer(new_job, context=self.get_serializer_context()).to_representation(new_job))
            else:
                data['job'] = new_job.id
                data['ignored_fields'] = self.sanitize_for_response(ignored_fields)
                data.update(JobSerializer(new_job, context=self.get_serializer_context()).to_representation(new_job))
            headers = {'Location': new_job.get_absolute_url(request)}
            return Response(data, status=status.HTTP_201_CREATED, headers=headers)


    def sanitize_for_response(self, data):
        '''
        Model objects cannot be serialized by DRF,
        this replaces objects with their ids for inclusion in response
        '''

        def display_value(val):
            if hasattr(val, 'id'):
                return val.id
            else:
                return val

        sanitized_data = {}
        for field_name, value in data.items():
            if isinstance(value, (set, list)):
                sanitized_data[field_name] = []
                for sub_value in value:
                    sanitized_data[field_name].append(display_value(sub_value))
            else:
                sanitized_data[field_name] = display_value(value)

        return sanitized_data


class JobTemplateSchedulesList(SubListCreateAPIView):

    view_name = _("Job Template Schedules")

    model = Schedule
    serializer_class = ScheduleSerializer
    parent_model = JobTemplate
    relationship = 'schedules'
    parent_key = 'unified_job_template'


class JobTemplateSurveySpec(GenericAPIView):

    model = JobTemplate
    obj_permission_type = 'admin'
    serializer_class = EmptySerializer

    ALLOWED_TYPES = {
        'text': six.string_types,
        'textarea': six.string_types,
        'password': six.string_types,
        'multiplechoice': six.string_types,
        'multiselect': six.string_types,
        'integer': int,
        'float': float
    }

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if not feature_enabled('surveys'):
            raise LicenseForbids(_('Your license does not allow '
                                   'adding surveys.'))

        return Response(obj.display_survey_spec())

    def post(self, request, *args, **kwargs):
        obj = self.get_object()

        # Sanity check: Are surveys available on this license?
        # If not, do not allow them to be used.
        if not feature_enabled('surveys'):
            raise LicenseForbids(_('Your license does not allow '
                                   'adding surveys.'))

        if not request.user.can_access(self.model, 'change', obj, None):
            raise PermissionDenied()
        response = self._validate_spec_data(request.data, obj.survey_spec)
        if response:
            return response
        obj.survey_spec = request.data
        obj.save(update_fields=['survey_spec'])
        return Response()

    @staticmethod
    def _validate_spec_data(new_spec, old_spec):
        schema_errors = {}
        for field, expect_type, type_label in [
                ('name', six.string_types, 'string'),
                ('description', six.string_types, 'string'),
                ('spec', list, 'list of items')]:
            if field not in new_spec:
                schema_errors['error'] = _("Field '{}' is missing from survey spec.").format(field)
            elif not isinstance(new_spec[field], expect_type):
                schema_errors['error'] = _("Expected {} for field '{}', received {} type.").format(
                    type_label, field, type(new_spec[field]).__name__)

        if isinstance(new_spec.get('spec', None), list) and len(new_spec["spec"]) < 1:
            schema_errors['error'] = _("'spec' doesn't contain any items.")

        if schema_errors:
            return Response(schema_errors, status=status.HTTP_400_BAD_REQUEST)

        variable_set = set()
        old_spec_dict = JobTemplate.pivot_spec(old_spec)
        for idx, survey_item in enumerate(new_spec["spec"]):
            context = dict(
                idx=six.text_type(idx),
                survey_item=survey_item
            )
            # General element validation
            if not isinstance(survey_item, dict):
                return Response(dict(error=_("Survey question %s is not a json object.") % str(idx)), status=status.HTTP_400_BAD_REQUEST)
            for field_name in ['type', 'question_name', 'variable', 'required']:
                if field_name not in survey_item:
                    return Response(dict(error=_("'{field_name}' missing from survey question {idx}").format(
                        field_name=field_name, **context
                    )), status=status.HTTP_400_BAD_REQUEST)
                val = survey_item[field_name]
                allow_types = six.string_types
                type_label = 'string'
                if field_name == 'required':
                    allow_types = bool
                    type_label = 'boolean'
                if not isinstance(val, allow_types):
                    return Response(dict(error=_("'{field_name}' in survey question {idx} expected to be {type_label}.").format(
                        field_name=field_name, type_label=type_label, **context
                    )))
            if survey_item['variable'] in variable_set:
                return Response(dict(error=_("'variable' '%(item)s' duplicated in survey question %(survey)s.") % {
                    'item': survey_item['variable'], 'survey': str(idx)}), status=status.HTTP_400_BAD_REQUEST)
            else:
                variable_set.add(survey_item['variable'])

            # Type-specific validation
            # validate question type <-> default type
            qtype = survey_item["type"]
            if qtype not in JobTemplateSurveySpec.ALLOWED_TYPES:
                return Response(dict(error=_(
                    "'{survey_item[type]}' in survey question {idx} is not one of '{allowed_types}' allowed question types."
                ).format(
                    allowed_types=', '.join(JobTemplateSurveySpec.ALLOWED_TYPES.keys()), **context
                )))
            if 'default' in survey_item:
                if not isinstance(survey_item['default'], JobTemplateSurveySpec.ALLOWED_TYPES[qtype]):
                    type_label = 'string'
                    if qtype in ['integer', 'float']:
                        type_label = qtype
                    return Response(dict(error=_(
                        "Default value {survey_item[default]} in survey question {idx} expected to be {type_label}."
                    ).format(
                        type_label=type_label, **context
                    )), status=status.HTTP_400_BAD_REQUEST)
            # additional type-specific properties, the UI provides these even
            # if not applicable to the question, TODO: request that they not do this
            for key in ['min', 'max']:
                if key in survey_item:
                    if survey_item[key] is not None and (not isinstance(survey_item[key], int)):
                        return Response(dict(error=_(
                            "The {min_or_max} limit in survey question {idx} expected to be integer."
                        ).format(min_or_max=key, **context)))
            if qtype in ['multiplechoice', 'multiselect'] and 'choices' not in survey_item:
                return Response(dict(error=_(
                    "Survey question {idx} of type {survey_item[type]} must specify choices.".format(**context)
                )))

            # Process encryption substitution
            if ("default" in survey_item and isinstance(survey_item['default'], six.string_types) and
                    survey_item['default'].startswith('$encrypted$')):
                # Submission expects the existence of encrypted DB value to replace given default
                if qtype != "password":
                    return Response(dict(error=_(
                        "$encrypted$ is a reserved keyword for password question defaults, "
                        "survey question {idx} is type {survey_item[type]}."
                    ).format(**context)), status=status.HTTP_400_BAD_REQUEST)
                old_element = old_spec_dict.get(survey_item['variable'], {})
                encryptedish_default_exists = False
                if 'default' in old_element:
                    old_default = old_element['default']
                    if isinstance(old_default, six.string_types):
                        if old_default.startswith('$encrypted$'):
                            encryptedish_default_exists = True
                        elif old_default == "":  # unencrypted blank string is allowed as DB value as special case
                            encryptedish_default_exists = True
                if not encryptedish_default_exists:
                    return Response(dict(error=_(
                        "$encrypted$ is a reserved keyword, may not be used for new default in position {idx}."
                    ).format(**context)), status=status.HTTP_400_BAD_REQUEST)
                survey_item['default'] = old_element['default']
            elif qtype == "password" and 'default' in survey_item:
                # Submission provides new encrypted default
                survey_item['default'] = encrypt_value(survey_item['default'])

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        if not request.user.can_access(self.model, 'delete', obj):
            raise PermissionDenied()
        obj.survey_spec = {}
        obj.save()
        return Response()


class JobTemplateActivityStreamList(ActivityStreamEnforcementMixin, SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = JobTemplate
    relationship = 'activitystream_set'
    search_fields = ('changes',)


class JobTemplateNotificationTemplatesAnyList(SubListCreateAttachDetachAPIView):

    model = NotificationTemplate
    serializer_class = NotificationTemplateSerializer
    parent_model = JobTemplate
    relationship = 'notification_templates_any'


class JobTemplateNotificationTemplatesErrorList(SubListCreateAttachDetachAPIView):

    model = NotificationTemplate
    serializer_class = NotificationTemplateSerializer
    parent_model = JobTemplate
    relationship = 'notification_templates_error'


class JobTemplateNotificationTemplatesSuccessList(SubListCreateAttachDetachAPIView):

    model = NotificationTemplate
    serializer_class = NotificationTemplateSerializer
    parent_model = JobTemplate
    relationship = 'notification_templates_success'


class JobTemplateCredentialsList(SubListCreateAttachDetachAPIView):

    model = Credential
    serializer_class = CredentialSerializer
    parent_model = JobTemplate
    relationship = 'credentials'

    def get_queryset(self):
        # Return the full list of credentials
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        sublist_qs = getattrd(parent, self.relationship)
        sublist_qs = sublist_qs.prefetch_related(
            'created_by', 'modified_by',
            'admin_role', 'use_role', 'read_role',
            'admin_role__parents', 'admin_role__members')
        return sublist_qs

    def is_valid_relation(self, parent, sub, created=False):
        if sub.unique_hash() in [cred.unique_hash() for cred in parent.credentials.all()]:
            return {"error": _("Cannot assign multiple {credential_type} credentials.").format(
                credential_type=sub.unique_hash(display=True))}
        kind = sub.credential_type.kind
        if kind not in ('ssh', 'vault', 'cloud', 'net'):
            return {'error': _('Cannot assign a Credential of kind `{}`.').format(kind)}

        return super(JobTemplateCredentialsList, self).is_valid_relation(parent, sub, created)


class JobTemplateExtraCredentialsList(JobTemplateCredentialsList):

    deprecated = True

    def get_queryset(self):
        sublist_qs = super(JobTemplateExtraCredentialsList, self).get_queryset()
        sublist_qs = sublist_qs.filter(credential_type__kind__in=['cloud', 'net'])
        return sublist_qs

    def is_valid_relation(self, parent, sub, created=False):
        valid = super(JobTemplateExtraCredentialsList, self).is_valid_relation(parent, sub, created)
        if sub.credential_type.kind not in ('cloud', 'net'):
            return {'error': _('Extra credentials must be network or cloud.')}
        return valid


class JobTemplateCallback(GenericAPIView):

    model = JobTemplate
    permission_classes = (JobTemplateCallbackPermission,)
    serializer_class = EmptySerializer
    parser_classes = api_settings.DEFAULT_PARSER_CLASSES + [FormParser]

    @csrf_exempt
    @transaction.non_atomic_requests
    def dispatch(self, *args, **kwargs):
        return super(JobTemplateCallback, self).dispatch(*args, **kwargs)

    def find_matching_hosts(self):
        '''
        Find the host(s) in the job template's inventory that match the remote
        host for the current request.
        '''
        # Find the list of remote host names/IPs to check.
        remote_hosts = set()
        for header in settings.REMOTE_HOST_HEADERS:
            for value in self.request.META.get(header, '').split(','):
                value = value.strip()
                if value:
                    remote_hosts.add(value)
        # Add the reverse lookup of IP addresses.
        for rh in list(remote_hosts):
            try:
                result = socket.gethostbyaddr(rh)
            except socket.herror:
                continue
            except socket.gaierror:
                continue
            remote_hosts.add(result[0])
            remote_hosts.update(result[1])
        # Filter out any .arpa results.
        for rh in list(remote_hosts):
            if rh.endswith('.arpa'):
                remote_hosts.remove(rh)
        if not remote_hosts:
            return set()
        # Find the host objects to search for a match.
        obj = self.get_object()
        hosts = obj.inventory.hosts.all()
        # Populate host_mappings
        host_mappings = {}
        for host in hosts:
            host_name = host.get_effective_host_name()
            host_mappings.setdefault(host_name, [])
            host_mappings[host_name].append(host)
        # Try finding direct match
        matches = set()
        for host_name in remote_hosts:
            if host_name in host_mappings:
                matches.update(host_mappings[host_name])
        if len(matches) == 1:
            return matches
        # Try to resolve forward addresses for each host to find matches.
        for host_name in host_mappings:
            try:
                result = socket.getaddrinfo(host_name, None)
                possible_ips = set(x[4][0] for x in result)
                possible_ips.discard(host_name)
                if possible_ips and possible_ips & remote_hosts:
                    matches.update(host_mappings[host_name])
            except socket.gaierror:
                pass
            except UnicodeError:
                pass
        return matches

    def get(self, request, *args, **kwargs):
        job_template = self.get_object()
        matching_hosts = self.find_matching_hosts()
        data = dict(
            host_config_key=job_template.host_config_key,
            matching_hosts=[x.name for x in matching_hosts],
        )
        if settings.DEBUG:
            d = dict([(k,v) for k,v in request.META.items()
                      if k.startswith('HTTP_') or k.startswith('REMOTE_')])
            data['request_meta'] = d
        return Response(data)

    def post(self, request, *args, **kwargs):
        extra_vars = None
        # Be careful here: content_type can look like '<content_type>; charset=blar'
        if request.content_type.startswith("application/json"):
            extra_vars = request.data.get("extra_vars", None)
        # Permission class should have already validated host_config_key.
        job_template = self.get_object()
        # Attempt to find matching hosts based on remote address.
        matching_hosts = self.find_matching_hosts()
        # If the host is not found, update the inventory before trying to
        # match again.
        inventory_sources_already_updated = []
        if len(matching_hosts) != 1:
            inventory_sources = job_template.inventory.inventory_sources.filter( update_on_launch=True)
            inventory_update_pks = set()
            for inventory_source in inventory_sources:
                if inventory_source.needs_update_on_launch:
                    # FIXME: Doesn't check for any existing updates.
                    inventory_update = inventory_source.create_inventory_update(
                        **{'_eager_fields': {'launch_type': 'callback'}}
                    )
                    inventory_update.signal_start()
                    inventory_update_pks.add(inventory_update.pk)
            inventory_update_qs = InventoryUpdate.objects.filter(pk__in=inventory_update_pks, status__in=('pending', 'waiting', 'running'))
            # Poll for the inventory updates we've started to complete.
            while inventory_update_qs.count():
                time.sleep(1.0)
                transaction.commit()
            # Ignore failed inventory updates here, only add successful ones
            # to the list to be excluded when running the job.
            for inventory_update in InventoryUpdate.objects.filter(pk__in=inventory_update_pks, status='successful'):
                inventory_sources_already_updated.append(inventory_update.inventory_source_id)
            matching_hosts = self.find_matching_hosts()
        # Check matching hosts.
        if not matching_hosts:
            data = dict(msg=_('No matching host could be found!'))
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        elif len(matching_hosts) > 1:
            data = dict(msg=_('Multiple hosts matched the request!'))
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        else:
            host = list(matching_hosts)[0]
        if not job_template.can_start_without_user_input(callback_extra_vars=extra_vars):
            data = dict(msg=_('Cannot start automatically, user input required!'))
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        limit = host.name

        # NOTE: We limit this to one job waiting per host per callblack to keep them from stacking crazily
        if Job.objects.filter(status__in=['pending', 'waiting', 'running'], job_template=job_template,
                              limit=limit).count() > 0:
            data = dict(msg=_('Host callback job already pending.'))
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        # Everything is fine; actually create the job.
        kv = {"limit": limit}
        kv.setdefault('_eager_fields', {})['launch_type'] = 'callback'
        if extra_vars is not None and job_template.ask_variables_on_launch:
            extra_vars_redacted, removed = extract_ansible_vars(extra_vars)
            kv['extra_vars'] = extra_vars_redacted
        kv['_prevent_slicing'] = True  # will only run against 1 host, so no point
        with transaction.atomic():
            job = job_template.create_job(**kv)

        # Send a signal to signify that the job should be started.
        result = job.signal_start(inventory_sources_already_updated=inventory_sources_already_updated)
        if not result:
            data = dict(msg=_('Error starting job!'))
            job.delete()
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        # Return the location of the new job.
        headers = {'Location': job.get_absolute_url(request=request)}
        return Response(status=status.HTTP_201_CREATED, headers=headers)


class JobTemplateJobsList(SubListCreateAPIView):

    model = Job
    serializer_class = JobListSerializer
    parent_model = JobTemplate
    relationship = 'jobs'
    parent_key = 'job_template'

    @property
    def allowed_methods(self):
        methods = super(JobTemplateJobsList, self).allowed_methods
        if get_request_version(getattr(self, 'request', None)) > 1:
            methods.remove('POST')
        return methods


class JobTemplateSliceWorkflowJobsList(SubListCreateAPIView):

    model = WorkflowJob
    serializer_class = WorkflowJobListSerializer
    parent_model = JobTemplate
    relationship = 'slice_workflow_jobs'
    parent_key = 'job_template'


class JobTemplateInstanceGroupsList(SubListAttachDetachAPIView):

    model = InstanceGroup
    serializer_class = InstanceGroupSerializer
    parent_model = JobTemplate
    relationship = 'instance_groups'


class JobTemplateAccessList(ResourceAccessList):

    model = User # needs to be User for AccessLists's
    parent_model = JobTemplate


class JobTemplateObjectRolesList(SubListAPIView):

    model = Role
    serializer_class = RoleSerializer
    parent_model = JobTemplate
    search_fields = ('role_field', 'content_type__model',)

    def get_queryset(self):
        po = self.get_parent_object()
        content_type = ContentType.objects.get_for_model(self.parent_model)
        return Role.objects.filter(content_type=content_type, object_id=po.pk)


class JobTemplateCopy(CopyAPIView):

    model = JobTemplate
    copy_return_serializer_class = JobTemplateSerializer


# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import time
import socket
import logging
from collections import OrderedDict

# Django
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _


# Django REST Framework
from rest_framework.parsers import FormParser
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework import status

# AWX
from awx.api.generics import * # noqa
from awx.main.models import * # noqa
from awx.main.utils import * # noqa

from awx.api.permissions import * # noqa
from awx.api.renderers import * # noqa
from awx.api.serializers import * # noqa
from awx.main.models.unified_jobs import ACTIVE_STATES
from awx.main.scheduler.tasks import run_job_complete

logger = logging.getLogger('awx.api.views')


class InventoryScriptList(ListCreateAPIView):

    model = CustomInventoryScript
    serializer_class = CustomInventoryScriptSerializer
    new_in_210 = True


class InventoryScriptDetail(RetrieveUpdateDestroyAPIView):

    model = CustomInventoryScript
    serializer_class = CustomInventoryScriptSerializer
    new_in_210 = True

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        can_delete = request.user.can_access(self.model, 'delete', instance)
        if not can_delete:
            raise PermissionDenied(_("Cannot delete inventory script."))
        for inv_src in InventorySource.objects.filter(source_script=instance):
            inv_src.source_script = None
            inv_src.save()
        return super(InventoryScriptDetail, self).destroy(request, *args, **kwargs)


class InventoryScriptObjectRolesList(SubListAPIView):

    model = Role
    serializer_class = RoleSerializer
    parent_model = CustomInventoryScript
    new_in_300 = True

    def get_queryset(self):
        po = self.get_parent_object()
        content_type = ContentType.objects.get_for_model(self.parent_model)
        return Role.objects.filter(content_type=content_type, object_id=po.pk)


class InventoryList(ListCreateAPIView):

    model = Inventory
    serializer_class = InventorySerializer
    capabilities_prefetch = ['admin', 'adhoc']

    def get_queryset(self):
        qs = Inventory.accessible_objects(self.request.user, 'read_role')
        qs = qs.select_related('admin_role', 'read_role', 'update_role', 'use_role', 'adhoc_role')
        qs = qs.prefetch_related('created_by', 'modified_by', 'organization')
        return qs


class InventoryDetail(ControlledByScmMixin, RetrieveUpdateDestroyAPIView):

    model = Inventory
    serializer_class = InventoryDetailSerializer

    def update(self, request, *args, **kwargs):
        obj = self.get_object()
        kind = self.request.data.get('kind') or kwargs.get('kind')

        # Do not allow changes to an Inventory kind.
        if kind is not None and obj.kind != kind:
            return self.http_method_not_allowed(request, *args, **kwargs)
        return super(InventoryDetail, self).update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        if not request.user.can_access(self.model, 'delete', obj):
            raise PermissionDenied()
        try:
            obj.schedule_deletion(getattr(request.user, 'id', None))
            return Response(status=status.HTTP_202_ACCEPTED)
        except RuntimeError, e:
            return Response(dict(error=_("{0}".format(e))), status=status.HTTP_400_BAD_REQUEST)


class InventoryActivityStreamList(ActivityStreamEnforcementMixin, SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = Inventory
    relationship = 'activitystream_set'
    new_in_145 = True

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model)
        return qs.filter(Q(inventory=parent) | Q(host__in=parent.hosts.all()) | Q(group__in=parent.groups.all()))


class InventoryInstanceGroupsList(SubListAttachDetachAPIView):

    model = InstanceGroup
    serializer_class = InstanceGroupSerializer
    parent_model = Inventory
    relationship = 'instance_groups'
    new_in_320 = True


class InventoryAccessList(ResourceAccessList):

    model = User # needs to be User for AccessLists's
    parent_model = Inventory
    new_in_300 = True


class InventoryObjectRolesList(SubListAPIView):

    model = Role
    serializer_class = RoleSerializer
    parent_model = Inventory
    new_in_300 = True

    def get_queryset(self):
        po = self.get_parent_object()
        content_type = ContentType.objects.get_for_model(self.parent_model)
        return Role.objects.filter(content_type=content_type, object_id=po.pk)


class InventoryJobTemplateList(SubListAPIView):

    model = JobTemplate
    serializer_class = JobTemplateSerializer
    parent_model = Inventory
    relationship = 'jobtemplates'
    new_in_300 = True

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model)
        return qs.filter(inventory=parent)


class InventoryHostsList(SubListCreateAttachDetachAPIView):

    model = Host
    serializer_class = HostSerializer
    parent_model = Inventory
    relationship = 'hosts'
    parent_key = 'inventory'
    capabilities_prefetch = ['inventory.admin']

    def get_queryset(self):
        inventory = self.get_parent_object()
        return getattrd(inventory, self.relationship).all()


class InventoryGroupsList(SubListCreateAttachDetachAPIView):

    model = Group
    serializer_class = GroupSerializer
    parent_model = Inventory
    relationship = 'groups'
    parent_key = 'inventory'


class InventoryRootGroupsList(SubListCreateAttachDetachAPIView):

    model = Group
    serializer_class = GroupSerializer
    parent_model = Inventory
    relationship = 'groups'
    parent_key = 'inventory'

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model).distinct() # need distinct for '&' operator
        return qs & parent.root_groups


class InventoryVariableData(BaseVariableData):

    model = Inventory
    serializer_class = InventoryVariableDataSerializer


class InventoryScriptView(RetrieveAPIView):

    model = Inventory
    serializer_class = InventoryScriptSerializer
    permission_classes = (TaskPermission,)
    filter_backends = ()

    def retrieve(self, request, *args, **kwargs):
        obj = self.get_object()
        hostname = request.query_params.get('host', '')
        show_all = bool(request.query_params.get('all', ''))
        if hostname:
            hosts_q = dict(name=hostname)
            if not show_all:
                hosts_q['enabled'] = True
            host = get_object_or_404(obj.hosts, **hosts_q)
            return Response(host.variables_dict)
        return Response(obj.get_script_data(
            hostvars=bool(request.query_params.get('hostvars', '')),
            show_all=show_all
        ))


class InventoryTreeView(RetrieveAPIView):

    model = Inventory
    serializer_class = GroupTreeSerializer
    filter_backends = ()
    new_in_13 = True

    def _populate_group_children(self, group_data, all_group_data_map, group_children_map):
        if 'children' in group_data:
            return
        group_data['children'] = []
        for child_id in group_children_map.get(group_data['id'], set()):
            group_data['children'].append(all_group_data_map[child_id])
        group_data['children'].sort(key=lambda x: x['name'])
        for child_data in group_data['children']:
            self._populate_group_children(child_data, all_group_data_map, group_children_map)

    def retrieve(self, request, *args, **kwargs):
        inventory = self.get_object()
        group_children_map = inventory.get_group_children_map()
        root_group_pks = inventory.root_groups.order_by('name').values_list('pk', flat=True)
        groups_qs = inventory.groups
        groups_qs = groups_qs.prefetch_related('inventory_sources')
        all_group_data = GroupSerializer(groups_qs, many=True).data
        all_group_data_map = dict((x['id'], x) for x in all_group_data)
        tree_data = [all_group_data_map[x] for x in root_group_pks]
        for group_data in tree_data:
            self._populate_group_children(group_data, all_group_data_map,
                                          group_children_map)
        return Response(tree_data)


class InventoryInventorySourcesList(SubListCreateAPIView):

    view_name = _('Inventory Source List')

    model = InventorySource
    serializer_class = InventorySourceSerializer
    parent_model = Inventory
    # Sometimes creation blocked by SCM inventory source restrictions
    always_allow_superuser = False
    relationship = 'inventory_sources'
    parent_key = 'inventory'
    new_in_320 = True


class InventoryInventorySourcesUpdate(RetrieveAPIView):
    view_name = _('Inventory Sources Update')

    model = Inventory
    obj_permission_type = 'start'
    serializer_class = InventorySourceUpdateSerializer
    permission_classes = (InventoryInventorySourcesUpdatePermission,)
    new_in_320 = True

    def retrieve(self, request, *args, **kwargs):
        inventory = self.get_object()
        update_data = []
        for inventory_source in inventory.inventory_sources.exclude(source=''):
            details = {'inventory_source': inventory_source.pk,
                       'can_update': inventory_source.can_update}
            update_data.append(details)
        return Response(update_data)

    def post(self, request, *args, **kwargs):
        inventory = self.get_object()
        update_data = []
        successes = 0
        failures = 0
        for inventory_source in inventory.inventory_sources.exclude(source=''):
            details = OrderedDict()
            details['inventory_source'] = inventory_source.pk
            details['status'] = None
            if inventory_source.can_update:
                update = inventory_source.update()
                details.update(InventoryUpdateSerializer(update, context=self.get_serializer_context()).to_representation(update))
                details['status'] = 'started'
                details['inventory_update'] = update.id
                successes += 1
            else:
                if not details.get('status'):
                    details['status'] = _('Could not start because `can_update` returned False')
                failures += 1
            update_data.append(details)
        if failures and successes:
            status_code = status.HTTP_202_ACCEPTED
        elif failures and not successes:
            status_code = status.HTTP_400_BAD_REQUEST
        elif not failures and not successes:
            return Response({'detail': _('No inventory sources to update.')},
                            status=status.HTTP_400_BAD_REQUEST)
        else:
            status_code = status.HTTP_200_OK
        return Response(update_data, status=status_code)


class InventorySourceList(ListCreateAPIView):

    model = InventorySource
    serializer_class = InventorySourceSerializer
    always_allow_superuser = False
    new_in_320 = True

    @property
    def allowed_methods(self):
        methods = super(InventorySourceList, self).allowed_methods
        if get_request_version(self.request) == 1:
            methods.remove('POST')
        return methods


class InventorySourceDetail(RetrieveUpdateDestroyAPIView):

    model = InventorySource
    serializer_class = InventorySourceSerializer
    new_in_14 = True

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        can_delete = request.user.can_access(InventorySource, 'delete', obj)
        if not can_delete:
            raise PermissionDenied(_("Cannot delete inventory source."))
        for pu in obj.inventory_updates.filter(status__in=['new', 'pending', 'waiting', 'running']):
            pu.cancel()
        return super(InventorySourceDetail, self).destroy(request, *args, **kwargs)


class InventorySourceSchedulesList(SubListCreateAPIView):

    view_name = _("Inventory Source Schedules")

    model = Schedule
    serializer_class = ScheduleSerializer
    parent_model = InventorySource
    relationship = 'schedules'
    parent_key = 'unified_job_template'
    new_in_148 = True


class InventorySourceActivityStreamList(ActivityStreamEnforcementMixin, SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = InventorySource
    relationship = 'activitystream_set'
    new_in_145 = True


class InventorySourceNotificationTemplatesAnyList(SubListCreateAttachDetachAPIView):

    model = NotificationTemplate
    serializer_class = NotificationTemplateSerializer
    parent_model = InventorySource
    relationship = 'notification_templates_any'
    new_in_300 = True

    def post(self, request, *args, **kwargs):
        parent = self.get_parent_object()
        if parent.source not in CLOUD_INVENTORY_SOURCES:
            return Response(dict(msg=_("Notification Templates can only be assigned when source is one of {}.")
                                 .format(CLOUD_INVENTORY_SOURCES, parent.source)),
                            status=status.HTTP_400_BAD_REQUEST)
        return super(InventorySourceNotificationTemplatesAnyList, self).post(request, *args, **kwargs)


class InventorySourceNotificationTemplatesErrorList(InventorySourceNotificationTemplatesAnyList):

    relationship = 'notification_templates_error'


class InventorySourceNotificationTemplatesSuccessList(InventorySourceNotificationTemplatesAnyList):

    relationship = 'notification_templates_success'


class InventorySourceHostsList(SubListAPIView):

    model = Host
    serializer_class = HostSerializer
    parent_model = InventorySource
    relationship = 'hosts'
    new_in_148 = True
    capabilities_prefetch = ['inventory.admin']


class InventorySourceGroupsList(SubListAPIView):

    model = Group
    serializer_class = GroupSerializer
    parent_model = InventorySource
    relationship = 'groups'
    new_in_148 = True


class InventorySourceUpdatesList(SubListAPIView):

    model = InventoryUpdate
    serializer_class = InventoryUpdateSerializer
    parent_model = InventorySource
    relationship = 'inventory_updates'
    new_in_14 = True


class InventorySourceUpdateView(RetrieveAPIView):

    model = InventorySource
    obj_permission_type = 'start'
    serializer_class = InventorySourceUpdateSerializer
    new_in_14 = True

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.can_update:
            update = obj.update()
            if not update:
                return Response({}, status=status.HTTP_400_BAD_REQUEST)
            else:
                headers = {'Location': update.get_absolute_url(request=request)}
                data = OrderedDict()
                data['inventory_update'] = update.id
                data.update(InventoryUpdateSerializer(update, context=self.get_serializer_context()).to_representation(update))
                return Response(data, status=status.HTTP_202_ACCEPTED, headers=headers)
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)


class InventoryUpdateList(ListAPIView):

    model = InventoryUpdate
    serializer_class = InventoryUpdateListSerializer

    def get_queryset(self):
        qs = super(InventoryUpdateList, self).get_queryset()
        # TODO: remove this defer in 3.3 when we implement https://github.com/ansible/ansible-tower/issues/5436
        qs = qs.defer('result_stdout_text')
        return qs


class InventoryUpdateDetail(UnifiedJobDeletionMixin, RetrieveDestroyAPIView):

    model = InventoryUpdate
    serializer_class = InventoryUpdateSerializer
    new_in_14 = True


class InventoryUpdateCancel(RetrieveAPIView):

    model = InventoryUpdate
    obj_permission_type = 'cancel'
    serializer_class = InventoryUpdateCancelSerializer
    new_in_14 = True

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.can_cancel:
            obj.cancel()
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)


class InventoryUpdateNotificationsList(SubListAPIView):

    model = Notification
    serializer_class = NotificationSerializer
    parent_model = InventoryUpdate
    relationship = 'notifications'
    new_in_300 = True


class JobTemplateList(ListCreateAPIView):

    model = JobTemplate
    metadata_class = JobTypeMetadata
    serializer_class = JobTemplateSerializer
    always_allow_superuser = False
    capabilities_prefetch = [
        'admin', 'execute',
        {'copy': ['project.use', 'inventory.use', 'credential.use', 'vault_credential.use']}
    ]

    def post(self, request, *args, **kwargs):
        ret = super(JobTemplateList, self).post(request, *args, **kwargs)
        if ret.status_code == 201:
            job_template = JobTemplate.objects.get(id=ret.data['id'])
            job_template.admin_role.members.add(request.user)
        return ret


class JobTemplateDetail(RetrieveUpdateDestroyAPIView):

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
            for p in obj.passwords_needed_to_start:
                data[p] = u''
            for v in obj.variables_needed_to_start:
                extra_vars.setdefault(v, u'')
            if extra_vars:
                data['extra_vars'] = extra_vars
            ask_for_vars_dict = obj._ask_for_vars_dict()
            ask_for_vars_dict.pop('extra_vars')
            if get_request_version(self.request) == 1:  # TODO: remove in 3.3
                ask_for_vars_dict.pop('extra_credentials')
            for field in ask_for_vars_dict:
                if not ask_for_vars_dict[field]:
                    data.pop(field, None)
                elif field == 'inventory' or field == 'credential':
                    data[field] = getattrd(obj, "%s.%s" % (field, 'id'), None)
                elif field == 'extra_credentials':
                    data[field] = [cred.id for cred in obj.extra_credentials.all()]
                else:
                    data[field] = getattr(obj, field)
        return data

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        ignored_fields = {}

        for fd in ('credential', 'vault_credential', 'inventory'):
            id_fd = '{}_id'.format(fd)
            if fd not in request.data and id_fd in request.data:
                request.data[fd] = request.data[id_fd]

        if get_request_version(self.request) == 1 and 'extra_credentials' in request.data:  # TODO: remove in 3.3
            if hasattr(request.data, '_mutable') and not request.data._mutable:
                request.data._mutable = True
            extra_creds = request.data.pop('extra_credentials', None)
            if extra_creds is not None:
                ignored_fields['extra_credentials'] = extra_creds

        passwords = {}
        serializer = self.serializer_class(instance=obj, data=request.data, context={'obj': obj, 'data': request.data, 'passwords': passwords})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        _accepted_or_ignored = obj._accept_or_ignore_job_kwargs(**request.data)
        prompted_fields = _accepted_or_ignored[0]
        ignored_fields.update(_accepted_or_ignored[1])

        for fd, model in (
                ('credential', Credential),
                ('vault_credential', Credential),
                ('inventory', Inventory)):
            if fd in prompted_fields and prompted_fields[fd] != getattrd(obj, '{}.pk'.format(fd), None):
                new_res = get_object_or_400(model, pk=get_pk_from_dict(prompted_fields, fd))
                use_role = getattr(new_res, 'use_role')
                if request.user not in use_role:
                    raise PermissionDenied()

        for cred in prompted_fields.get('extra_credentials', []):
            new_credential = get_object_or_400(Credential, pk=cred)
            if request.user not in new_credential.use_role:
                raise PermissionDenied()

        new_job = obj.create_unified_job(**prompted_fields)
        result = new_job.signal_start(**passwords)

        if not result:
            data = dict(passwords_needed_to_start=new_job.passwords_needed_to_start)
            new_job.delete()
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        else:
            data = OrderedDict()
            data['job'] = new_job.id
            data['ignored_fields'] = ignored_fields
            data.update(JobSerializer(new_job, context=self.get_serializer_context()).to_representation(new_job))
            return Response(data, status=status.HTTP_201_CREATED)


class JobTemplateSchedulesList(SubListCreateAPIView):

    view_name = _("Job Template Schedules")

    model = Schedule
    serializer_class = ScheduleSerializer
    parent_model = JobTemplate
    relationship = 'schedules'
    parent_key = 'unified_job_template'
    new_in_148 = True


class JobTemplateSurveySpec(GenericAPIView):

    model = JobTemplate
    obj_permission_type = 'admin'
    serializer_class = EmptySerializer
    new_in_210 = True

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if not feature_enabled('surveys'):
            raise LicenseForbids(_('Your license does not allow '
                                   'adding surveys.'))
        survey_spec = obj.survey_spec
        for pos, field in enumerate(survey_spec.get('spec', [])):
            if field.get('type') == 'password':
                if 'default' in field and field['default']:
                    field['default'] = '$encrypted$'

        return Response(survey_spec)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()

        # Sanity check: Are surveys available on this license?
        # If not, do not allow them to be used.
        if not feature_enabled('surveys'):
            raise LicenseForbids(_('Your license does not allow '
                                   'adding surveys.'))

        if not request.user.can_access(self.model, 'change', obj, None):
            raise PermissionDenied()
        new_spec = request.data
        if "name" not in new_spec:
            return Response(dict(error=_("'name' missing from survey spec.")), status=status.HTTP_400_BAD_REQUEST)
        if "description" not in new_spec:
            return Response(dict(error=_("'description' missing from survey spec.")), status=status.HTTP_400_BAD_REQUEST)
        if "spec" not in new_spec:
            return Response(dict(error=_("'spec' missing from survey spec.")), status=status.HTTP_400_BAD_REQUEST)
        if not isinstance(new_spec["spec"], list):
            return Response(dict(error=_("'spec' must be a list of items.")), status=status.HTTP_400_BAD_REQUEST)
        if len(new_spec["spec"]) < 1:
            return Response(dict(error=_("'spec' doesn't contain any items.")), status=status.HTTP_400_BAD_REQUEST)

        idx = 0
        variable_set = set()
        for survey_item in new_spec["spec"]:
            if not isinstance(survey_item, dict):
                return Response(dict(error=_("Survey question %s is not a json object.") % str(idx)), status=status.HTTP_400_BAD_REQUEST)
            if "type" not in survey_item:
                return Response(dict(error=_("'type' missing from survey question %s.") % str(idx)), status=status.HTTP_400_BAD_REQUEST)
            if "question_name" not in survey_item:
                return Response(dict(error=_("'question_name' missing from survey question %s.") % str(idx)), status=status.HTTP_400_BAD_REQUEST)
            if "variable" not in survey_item:
                return Response(dict(error=_("'variable' missing from survey question %s.") % str(idx)), status=status.HTTP_400_BAD_REQUEST)
            if survey_item['variable'] in variable_set:
                return Response(dict(error=_("'variable' '%(item)s' duplicated in survey question %(survey)s.") % {
                    'item': survey_item['variable'], 'survey': str(idx)}), status=status.HTTP_400_BAD_REQUEST)
            else:
                variable_set.add(survey_item['variable'])
            if "required" not in survey_item:
                return Response(dict(error=_("'required' missing from survey question %s.") % str(idx)), status=status.HTTP_400_BAD_REQUEST)

            if survey_item["type"] == "password":
                if survey_item.get("default") and survey_item["default"].startswith('$encrypted$'):
                    if not obj.survey_spec:
                        return Response(dict(error=_("$encrypted$ is reserved keyword and may not be used as a default for password {}.".format(str(idx)))),
                                        status=status.HTTP_400_BAD_REQUEST)
                    else:
                        old_spec = obj.survey_spec
                        for old_item in old_spec['spec']:
                            if old_item['variable'] == survey_item['variable']:
                                survey_item['default'] = old_item['default']
            idx += 1

        obj.survey_spec = new_spec
        obj.save(update_fields=['survey_spec'])
        return Response()

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        if not request.user.can_access(self.model, 'delete', obj):
            raise PermissionDenied()
        obj.survey_spec = {}
        obj.save()
        return Response()


class WorkflowJobTemplateSurveySpec(WorkflowsEnforcementMixin, JobTemplateSurveySpec):

    model = WorkflowJobTemplate
    new_in_310 = True


class JobTemplateActivityStreamList(ActivityStreamEnforcementMixin, SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = JobTemplate
    relationship = 'activitystream_set'
    new_in_145 = True


class JobTemplateNotificationTemplatesAnyList(SubListCreateAttachDetachAPIView):

    model = NotificationTemplate
    serializer_class = NotificationTemplateSerializer
    parent_model = JobTemplate
    relationship = 'notification_templates_any'
    new_in_300 = True


class JobTemplateNotificationTemplatesErrorList(SubListCreateAttachDetachAPIView):

    model = NotificationTemplate
    serializer_class = NotificationTemplateSerializer
    parent_model = JobTemplate
    relationship = 'notification_templates_error'
    new_in_300 = True


class JobTemplateNotificationTemplatesSuccessList(SubListCreateAttachDetachAPIView):

    model = NotificationTemplate
    serializer_class = NotificationTemplateSerializer
    parent_model = JobTemplate
    relationship = 'notification_templates_success'
    new_in_300 = True


class JobTemplateExtraCredentialsList(SubListCreateAttachDetachAPIView):

    model = Credential
    serializer_class = CredentialSerializer
    parent_model = JobTemplate
    relationship = 'extra_credentials'
    new_in_320 = True
    new_in_api_v2 = True

    def get_queryset(self):
        # Return the full list of extra_credentials
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        sublist_qs = getattrd(parent, self.relationship)
        sublist_qs = sublist_qs.prefetch_related(
            'created_by', 'modified_by',
            'admin_role', 'use_role', 'read_role',
            'admin_role__parents', 'admin_role__members')
        return sublist_qs

    def is_valid_relation(self, parent, sub, created=False):
        current_extra_types = [
            cred.credential_type.pk for cred in parent.extra_credentials.all()
        ]
        if sub.credential_type.pk in current_extra_types:
            return {'error': _('Cannot assign multiple %s credentials.' % sub.credential_type.name)}

        if sub.credential_type.kind not in ('net', 'cloud'):
            return {'error': _('Extra credentials must be network or cloud.')}
        return super(JobTemplateExtraCredentialsList, self).is_valid_relation(parent, sub, created)


class JobTemplateLabelList(DeleteLastUnattachLabelMixin, SubListCreateAttachDetachAPIView):

    model = Label
    serializer_class = LabelSerializer
    parent_model = JobTemplate
    relationship = 'labels'
    new_in_300 = True

    def post(self, request, *args, **kwargs):
        # If a label already exists in the database, attach it instead of erroring out
        # that it already exists
        if 'id' not in request.data and 'name' in request.data and 'organization' in request.data:
            existing = Label.objects.filter(name=request.data['name'], organization_id=request.data['organization'])
            if existing.exists():
                existing = existing[0]
                request.data['id'] = existing.id
                del request.data['name']
                del request.data['organization']
        if Label.objects.filter(unifiedjobtemplate_labels=self.kwargs['pk']).count() > 100:
            return Response(dict(msg=_('Maximum number of labels for {} reached.'.format(
                self.parent_model._meta.verbose_name_raw))), status=status.HTTP_400_BAD_REQUEST)
        return super(JobTemplateLabelList, self).post(request, *args, **kwargs)


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
                    inventory_update = inventory_source.create_inventory_update(launch_type='callback')
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
        kv = {"limit": limit, "launch_type": 'callback'}
        if extra_vars is not None and job_template.ask_variables_on_launch:
            extra_vars_redacted, removed = extract_ansible_vars(extra_vars)
            kv['extra_vars'] = extra_vars_redacted
        with transaction.atomic():
            job = job_template.create_job(**kv)

        # Send a signal to celery that the job should be started.
        result = job.signal_start(inventory_sources_already_updated=inventory_sources_already_updated)
        if not result:
            data = dict(msg=_('Error starting job!'))
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


class JobTemplateInstanceGroupsList(SubListAttachDetachAPIView):

    model = InstanceGroup
    serializer_class = InstanceGroupSerializer
    parent_model = JobTemplate
    relationship = 'instance_groups'
    new_in_320 = True


class JobTemplateAccessList(ResourceAccessList):

    model = User # needs to be User for AccessLists's
    parent_model = JobTemplate
    new_in_300 = True


class JobTemplateObjectRolesList(SubListAPIView):

    model = Role
    serializer_class = RoleSerializer
    parent_model = JobTemplate
    new_in_300 = True

    def get_queryset(self):
        po = self.get_parent_object()
        content_type = ContentType.objects.get_for_model(self.parent_model)
        return Role.objects.filter(content_type=content_type, object_id=po.pk)


class WorkflowJobNodeList(WorkflowsEnforcementMixin, ListAPIView):

    model = WorkflowJobNode
    serializer_class = WorkflowJobNodeListSerializer
    new_in_310 = True


class WorkflowJobNodeDetail(WorkflowsEnforcementMixin, RetrieveAPIView):

    model = WorkflowJobNode
    serializer_class = WorkflowJobNodeDetailSerializer
    new_in_310 = True


class WorkflowJobTemplateNodeList(WorkflowsEnforcementMixin, ListCreateAPIView):

    model = WorkflowJobTemplateNode
    serializer_class = WorkflowJobTemplateNodeListSerializer
    new_in_310 = True


class WorkflowJobTemplateNodeDetail(WorkflowsEnforcementMixin, RetrieveUpdateDestroyAPIView):

    model = WorkflowJobTemplateNode
    serializer_class = WorkflowJobTemplateNodeDetailSerializer
    new_in_310 = True

    def update_raw_data(self, data):
        for fd in ['job_type', 'job_tags', 'skip_tags', 'limit', 'skip_tags']:
            data[fd] = None
        try:
            obj = self.get_object()
            data.update(obj.char_prompts)
        except Exception:
            pass
        return super(WorkflowJobTemplateNodeDetail, self).update_raw_data(data)


class WorkflowJobTemplateNodeChildrenBaseList(WorkflowsEnforcementMixin, EnforceParentRelationshipMixin, SubListCreateAttachDetachAPIView):

    model = WorkflowJobTemplateNode
    serializer_class = WorkflowJobTemplateNodeListSerializer
    always_allow_superuser = True
    parent_model = WorkflowJobTemplateNode
    relationship = ''
    enforce_parent_relationship = 'workflow_job_template'
    new_in_310 = True

    '''
    Limit the set of WorkflowJobTemplateNodes to the related nodes of specified by
    'relationship'
    '''
    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        return getattr(parent, self.relationship).all()

    def is_valid_relation(self, parent, sub, created=False):
        mutex_list = ('success_nodes', 'failure_nodes') if self.relationship == 'always_nodes' else ('always_nodes',)
        for relation in mutex_list:
            if getattr(parent, relation).all().exists():
                return {'Error': _('Cannot associate {0} when {1} have been associated.').format(self.relationship, relation)}

        if created:
            return None

        workflow_nodes = parent.workflow_job_template.workflow_job_template_nodes.all().\
            prefetch_related('success_nodes', 'failure_nodes', 'always_nodes')
        graph = {}
        for workflow_node in workflow_nodes:
            graph[workflow_node.pk] = dict(node_object=workflow_node, metadata={'parent': None, 'traversed': False})

        find = False
        for node_type in ['success_nodes', 'failure_nodes', 'always_nodes']:
            for workflow_node in workflow_nodes:
                parent_node = graph[workflow_node.pk]
                related_nodes = getattr(parent_node['node_object'], node_type).all()
                for related_node in related_nodes:
                    sub_node = graph[related_node.pk]
                    sub_node['metadata']['parent'] = parent_node
                    if not find and parent == workflow_node and sub == related_node and self.relationship == node_type:
                        find = True
        if not find:
            sub_node = graph[sub.pk]
            parent_node = graph[parent.pk]
            if sub_node['metadata']['parent'] is not None:
                return {"Error": _("Multiple parent relationship not allowed.")}
            sub_node['metadata']['parent'] = parent_node
            iter_node = sub_node
            while iter_node is not None:
                if iter_node['metadata']['traversed']:
                    return {"Error": _("Cycle detected.")}
                iter_node['metadata']['traversed'] = True
                iter_node = iter_node['metadata']['parent']

        return None


class WorkflowJobTemplateNodeSuccessNodesList(WorkflowJobTemplateNodeChildrenBaseList):
    relationship = 'success_nodes'


class WorkflowJobTemplateNodeFailureNodesList(WorkflowJobTemplateNodeChildrenBaseList):
    relationship = 'failure_nodes'


class WorkflowJobTemplateNodeAlwaysNodesList(WorkflowJobTemplateNodeChildrenBaseList):
    relationship = 'always_nodes'


class WorkflowJobNodeChildrenBaseList(WorkflowsEnforcementMixin, SubListAPIView):

    model = WorkflowJobNode
    serializer_class = WorkflowJobNodeListSerializer
    parent_model = WorkflowJobNode
    relationship = ''
    new_in_310 = True

    #
    #Limit the set of WorkflowJobeNodes to the related nodes of specified by
    #'relationship'
    #
    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        return getattr(parent, self.relationship).all()


class WorkflowJobNodeSuccessNodesList(WorkflowJobNodeChildrenBaseList):
    relationship = 'success_nodes'


class WorkflowJobNodeFailureNodesList(WorkflowJobNodeChildrenBaseList):
    relationship = 'failure_nodes'


class WorkflowJobNodeAlwaysNodesList(WorkflowJobNodeChildrenBaseList):
    relationship = 'always_nodes'


class WorkflowJobTemplateList(WorkflowsEnforcementMixin, ListCreateAPIView):

    model = WorkflowJobTemplate
    serializer_class = WorkflowJobTemplateListSerializer
    always_allow_superuser = False
    new_in_310 = True


class WorkflowJobTemplateDetail(WorkflowsEnforcementMixin, RetrieveUpdateDestroyAPIView):

    model = WorkflowJobTemplate
    serializer_class = WorkflowJobTemplateSerializer
    always_allow_superuser = False
    new_in_310 = True


class WorkflowJobTemplateCopy(WorkflowsEnforcementMixin, GenericAPIView):

    model = WorkflowJobTemplate
    serializer_class = EmptySerializer
    new_in_310 = True

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        can_copy, messages = request.user.can_access_with_errors(self.model, 'copy', obj)
        data = OrderedDict([
            ('can_copy', can_copy), ('can_copy_without_user_input', can_copy),
            ('templates_unable_to_copy', [] if can_copy else ['all']),
            ('credentials_unable_to_copy', [] if can_copy else ['all']),
            ('inventories_unable_to_copy', [] if can_copy else ['all'])
        ])
        if messages and can_copy:
            data['can_copy_without_user_input'] = False
            data.update(messages)
        return Response(data)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if not request.user.can_access(self.model, 'copy', obj):
            raise PermissionDenied()
        new_obj = obj.user_copy(request.user)
        if request.user not in new_obj.admin_role:
            new_obj.admin_role.members.add(request.user)
        data = OrderedDict()
        data.update(WorkflowJobTemplateSerializer(
            new_obj, context=self.get_serializer_context()).to_representation(new_obj))
        return Response(data, status=status.HTTP_201_CREATED)


class WorkflowJobTemplateLabelList(WorkflowsEnforcementMixin, JobTemplateLabelList):
    parent_model = WorkflowJobTemplate
    new_in_310 = True


class WorkflowJobTemplateLaunch(WorkflowsEnforcementMixin, RetrieveAPIView):


    model = WorkflowJobTemplate
    obj_permission_type = 'start'
    serializer_class = WorkflowJobLaunchSerializer
    new_in_310 = True
    always_allow_superuser = False

    def update_raw_data(self, data):
        try:
            obj = self.get_object()
        except PermissionDenied:
            return data
        extra_vars = data.pop('extra_vars', None) or {}
        if obj:
            for v in obj.variables_needed_to_start:
                extra_vars.setdefault(v, u'')
            if extra_vars:
                data['extra_vars'] = extra_vars
        return data

    def post(self, request, *args, **kwargs):
        obj = self.get_object()

        serializer = self.serializer_class(instance=obj, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        prompted_fields, ignored_fields = obj._accept_or_ignore_job_kwargs(**request.data)

        new_job = obj.create_unified_job(**prompted_fields)
        new_job.signal_start()

        data = OrderedDict()
        data['workflow_job'] = new_job.id
        data['ignored_fields'] = ignored_fields
        data.update(WorkflowJobSerializer(new_job, context=self.get_serializer_context()).to_representation(new_job))
        return Response(data, status=status.HTTP_201_CREATED)


class WorkflowJobRelaunch(WorkflowsEnforcementMixin, GenericAPIView):

    model = WorkflowJob
    obj_permission_type = 'start'
    serializer_class = EmptySerializer
    new_in_310 = True

    def check_object_permissions(self, request, obj):
        if request.method == 'POST' and obj:
            relaunch_perm, messages = request.user.can_access_with_errors(self.model, 'start', obj)
            if not relaunch_perm and 'workflow_job_template' in messages:
                self.permission_denied(request, message=messages['workflow_job_template'])
        return super(WorkflowJobRelaunch, self).check_object_permissions(request, obj)

    def get(self, request, *args, **kwargs):
        return Response({})

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        new_workflow_job = obj.create_relaunch_workflow_job()
        new_workflow_job.signal_start()

        data = WorkflowJobSerializer(new_workflow_job, context=self.get_serializer_context()).data
        headers = {'Location': new_workflow_job.get_absolute_url(request=request)}
        return Response(data, status=status.HTTP_201_CREATED, headers=headers)


class WorkflowJobTemplateWorkflowNodesList(WorkflowsEnforcementMixin, SubListCreateAPIView):

    model = WorkflowJobTemplateNode
    serializer_class = WorkflowJobTemplateNodeListSerializer
    parent_model = WorkflowJobTemplate
    relationship = 'workflow_job_template_nodes'
    parent_key = 'workflow_job_template'
    new_in_310 = True

    def update_raw_data(self, data):
        for fd in ['job_type', 'job_tags', 'skip_tags', 'limit', 'skip_tags']:
            data[fd] = None
        return super(WorkflowJobTemplateWorkflowNodesList, self).update_raw_data(data)

    def get_queryset(self):
        return super(WorkflowJobTemplateWorkflowNodesList, self).get_queryset().order_by('id')


class WorkflowJobTemplateJobsList(WorkflowsEnforcementMixin, SubListAPIView):

    model = WorkflowJob
    serializer_class = WorkflowJobListSerializer
    parent_model = WorkflowJobTemplate
    relationship = 'workflow_jobs'
    parent_key = 'workflow_job_template'
    new_in_310 = True


class WorkflowJobTemplateSchedulesList(WorkflowsEnforcementMixin, SubListCreateAPIView):

    view_name = _("Workflow Job Template Schedules")

    model = Schedule
    serializer_class = ScheduleSerializer
    parent_model = WorkflowJobTemplate
    relationship = 'schedules'
    parent_key = 'unified_job_template'
    new_in_310 = True


class WorkflowJobTemplateNotificationTemplatesAnyList(WorkflowsEnforcementMixin, SubListCreateAttachDetachAPIView):

    model = NotificationTemplate
    serializer_class = NotificationTemplateSerializer
    parent_model = WorkflowJobTemplate
    relationship = 'notification_templates_any'
    new_in_310 = True


class WorkflowJobTemplateNotificationTemplatesErrorList(WorkflowsEnforcementMixin, SubListCreateAttachDetachAPIView):

    model = NotificationTemplate
    serializer_class = NotificationTemplateSerializer
    parent_model = WorkflowJobTemplate
    relationship = 'notification_templates_error'
    new_in_310 = True


class WorkflowJobTemplateNotificationTemplatesSuccessList(WorkflowsEnforcementMixin, SubListCreateAttachDetachAPIView):

    model = NotificationTemplate
    serializer_class = NotificationTemplateSerializer
    parent_model = WorkflowJobTemplate
    relationship = 'notification_templates_success'
    new_in_310 = True


class WorkflowJobTemplateAccessList(WorkflowsEnforcementMixin, ResourceAccessList):

    model = User # needs to be User for AccessLists's
    parent_model = WorkflowJobTemplate
    new_in_310 = True


class WorkflowJobTemplateObjectRolesList(WorkflowsEnforcementMixin, SubListAPIView):

    model = Role
    serializer_class = RoleSerializer
    parent_model = WorkflowJobTemplate
    new_in_310 = True

    def get_queryset(self):
        po = self.get_parent_object()
        content_type = ContentType.objects.get_for_model(self.parent_model)
        return Role.objects.filter(content_type=content_type, object_id=po.pk)


class WorkflowJobTemplateActivityStreamList(WorkflowsEnforcementMixin, ActivityStreamEnforcementMixin, SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = WorkflowJobTemplate
    relationship = 'activitystream_set'
    new_in_310 = True

    def get_queryset(self):
        parent = self.get_parent_object()
        self.check_parent_access(parent)
        qs = self.request.user.get_queryset(self.model)
        return qs.filter(Q(workflow_job_template=parent) |
                         Q(workflow_job_template_node__workflow_job_template=parent)).distinct()


class WorkflowJobList(WorkflowsEnforcementMixin, ListCreateAPIView):

    model = WorkflowJob
    serializer_class = WorkflowJobListSerializer
    new_in_310 = True


class WorkflowJobDetail(WorkflowsEnforcementMixin, UnifiedJobDeletionMixin, RetrieveDestroyAPIView):

    model = WorkflowJob
    serializer_class = WorkflowJobSerializer
    new_in_310 = True


class WorkflowJobWorkflowNodesList(WorkflowsEnforcementMixin, SubListAPIView):

    model = WorkflowJobNode
    serializer_class = WorkflowJobNodeListSerializer
    always_allow_superuser = True
    parent_model = WorkflowJob
    relationship = 'workflow_job_nodes'
    parent_key = 'workflow_job'
    new_in_310 = True

    def get_queryset(self):
        return super(WorkflowJobWorkflowNodesList, self).get_queryset().order_by('id')


class WorkflowJobCancel(WorkflowsEnforcementMixin, RetrieveAPIView):

    model = WorkflowJob
    obj_permission_type = 'cancel'
    serializer_class = WorkflowJobCancelSerializer
    new_in_310 = True

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.can_cancel:
            obj.cancel()
            #TODO: Figure out whether an immediate schedule is needed.
            run_job_complete.delay(obj.id)
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return self.http_method_not_allowed(request, *args, **kwargs)


class WorkflowJobNotificationsList(WorkflowsEnforcementMixin, SubListAPIView):

    model = Notification
    serializer_class = NotificationSerializer
    parent_model = WorkflowJob
    relationship = 'notifications'
    new_in_310 = True


class WorkflowJobActivityStreamList(WorkflowsEnforcementMixin, ActivityStreamEnforcementMixin, SubListAPIView):

    model = ActivityStream
    serializer_class = ActivityStreamSerializer
    parent_model = WorkflowJob
    relationship = 'activitystream_set'
    new_in_310 = True


class SystemJobTemplateList(ListAPIView):

    model = SystemJobTemplate
    serializer_class = SystemJobTemplateSerializer
    new_in_210 = True

    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser and not request.user.is_system_auditor:
            raise PermissionDenied(_("Superuser privileges needed."))
        return super(SystemJobTemplateList, self).get(request, *args, **kwargs)


class SystemJobTemplateDetail(RetrieveAPIView):

    model = SystemJobTemplate
    serializer_class = SystemJobTemplateSerializer
    new_in_210 = True


class SystemJobTemplateLaunch(GenericAPIView):

    model = SystemJobTemplate
    obj_permission_type = 'start'
    serializer_class = EmptySerializer
    new_in_210 = True

    def get(self, request, *args, **kwargs):
        return Response({})

    def post(self, request, *args, **kwargs):
        obj = self.get_object()

        new_job = obj.create_unified_job(extra_vars=request.data.get('extra_vars', {}))
        new_job.signal_start()
        data = OrderedDict()
        data['system_job'] = new_job.id
        data.update(SystemJobSerializer(new_job, context=self.get_serializer_context()).to_representation(new_job))
        return Response(data, status=status.HTTP_201_CREATED)


class SystemJobTemplateSchedulesList(SubListCreateAPIView):

    view_name = _("System Job Template Schedules")

    model = Schedule
    serializer_class = ScheduleSerializer
    parent_model = SystemJobTemplate
    relationship = 'schedules'
    parent_key = 'unified_job_template'
    new_in_210 = True


class SystemJobTemplateJobsList(SubListAPIView):

    model = SystemJob
    serializer_class = SystemJobListSerializer
    parent_model = SystemJobTemplate
    relationship = 'jobs'
    parent_key = 'system_job_template'
    new_in_210 = True


class SystemJobTemplateNotificationTemplatesAnyList(SubListCreateAttachDetachAPIView):

    model = NotificationTemplate
    serializer_class = NotificationTemplateSerializer
    parent_model = SystemJobTemplate
    relationship = 'notification_templates_any'
    new_in_300 = True


class SystemJobTemplateNotificationTemplatesErrorList(SubListCreateAttachDetachAPIView):

    model = NotificationTemplate
    serializer_class = NotificationTemplateSerializer
    parent_model = SystemJobTemplate
    relationship = 'notification_templates_error'
    new_in_300 = True


class SystemJobTemplateNotificationTemplatesSuccessList(SubListCreateAttachDetachAPIView):

    model = NotificationTemplate
    serializer_class = NotificationTemplateSerializer
    parent_model = SystemJobTemplate
    relationship = 'notification_templates_success'
    new_in_300 = True


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


class JobExtraCredentialsList(SubListAPIView):

    model = Credential
    serializer_class = CredentialSerializer
    parent_model = Job
    relationship = 'extra_credentials'
    new_in_320 = True
    new_in_api_v2 = True


class JobLabelList(SubListAPIView):

    model = Label
    serializer_class = LabelSerializer
    parent_model = Job
    relationship = 'labels'
    parent_key = 'job'
    new_in_300 = True


class WorkflowJobLabelList(WorkflowsEnforcementMixin, JobLabelList):
    parent_model = WorkflowJob
    new_in_310 = True


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


class HostJobHostSummariesList(BaseJobHostSummariesList):

    parent_model = Host


class GroupJobHostSummariesList(BaseJobHostSummariesList):

    parent_model = Group


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


class HostJobEventsList(BaseJobEventsList):

    parent_model = Host

    def get_queryset(self):
        parent_obj = self.get_parent_object()
        self.check_parent_access(parent_obj)
        qs = self.request.user.get_queryset(self.model).filter(
            Q(host=parent_obj) | Q(hosts=parent_obj)).distinct()
        return qs


class GroupJobEventsList(BaseJobEventsList):

    parent_model = Group


class JobJobEventsList(BaseJobEventsList):

    parent_model = Job

    def get_queryset(self):
        job = self.get_parent_object()
        self.check_parent_access(job)
        qs = job.job_events
        qs = qs.select_related('host')
        qs = qs.prefetch_related('hosts', 'children')
        return qs.all()


class AdHocCommandList(ListCreateAPIView):

    model = AdHocCommand
    serializer_class = AdHocCommandListSerializer
    new_in_220 = True
    always_allow_superuser = False

    @csrf_exempt
    @transaction.non_atomic_requests
    def dispatch(self, *args, **kwargs):
        return super(AdHocCommandList, self).dispatch(*args, **kwargs)

    def update_raw_data(self, data):
        # Hide inventory and limit fields from raw data, since they will be set
        # automatically by sub list create view.
        parent_model = getattr(self, 'parent_model', None)
        if parent_model in (Host, Group):
            data.pop('inventory', None)
            data.pop('limit', None)
        return super(AdHocCommandList, self).update_raw_data(data)

    def create(self, request, *args, **kwargs):
        # Inject inventory ID and limit if parent objects is a host/group.
        if hasattr(self, 'get_parent_object') and not getattr(self, 'parent_key', None):
            data = request.data
            # HACK: Make request data mutable.
            if getattr(data, '_mutable', None) is False:
                data._mutable = True
            parent_obj = self.get_parent_object()
            if isinstance(parent_obj, (Host, Group)):
                data['inventory'] = parent_obj.inventory_id
                data['limit'] = parent_obj.name

        # Check for passwords needed before creating ad hoc command.
        credential_pk = get_pk_from_dict(request.data, 'credential')
        if credential_pk:
            credential = get_object_or_400(Credential, pk=credential_pk)
            needed = credential.passwords_needed
            provided = dict([(field, request.data.get(field, '')) for field in needed])
            if not all(provided.values()):
                data = dict(passwords_needed_to_start=needed)
                return Response(data, status=status.HTTP_400_BAD_REQUEST)

        response = super(AdHocCommandList, self).create(request, *args, **kwargs)
        if response.status_code != status.HTTP_201_CREATED:
            return response

        # Start ad hoc command running when created.
        ad_hoc_command = get_object_or_400(self.model, pk=response.data['id'])
        result = ad_hoc_command.signal_start(**request.data)
        if not result:
            data = dict(passwords_needed_to_start=ad_hoc_command.passwords_needed_to_start)
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        return response


class InventoryAdHocCommandsList(AdHocCommandList, SubListCreateAPIView):

    parent_model = Inventory
    relationship = 'ad_hoc_commands'
    parent_key = 'inventory'


class InventoryUpdateStdout(UnifiedJobStdout):

    model = InventoryUpdate

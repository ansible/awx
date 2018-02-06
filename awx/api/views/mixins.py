from django.utils.translation import ugettext_lazy as _
from django.db.models import Count, F

from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import SAFE_METHODS

from awx.api.versioning import get_request_version
from awx.main.models import (
    Inventory,
    Project,
    JobTemplate,
    Team,
)

from awx.main.models.unified_jobs import ACTIVE_STATES
from awx.conf.license import (
    feature_enabled,
    LicenseForbids,
)
from awx.main.utils import parse_yaml_or_json


class ActivityStreamEnforcementMixin(object):
    '''
    Mixin to check that license supports activity streams.
    '''
    def check_permissions(self, request):
        if not feature_enabled('activity_streams'):
            raise LicenseForbids(_('Your license does not allow use of the activity stream.'))
        return super(ActivityStreamEnforcementMixin, self).check_permissions(request)


class SystemTrackingEnforcementMixin(object):
    '''
    Mixin to check that license supports system tracking.
    '''
    def check_permissions(self, request):
        if not feature_enabled('system_tracking'):
            raise LicenseForbids(_('Your license does not permit use of system tracking.'))
        return super(SystemTrackingEnforcementMixin, self).check_permissions(request)


class WorkflowsEnforcementMixin(object):
    '''
    Mixin to check that license supports workflows.
    '''
    def check_permissions(self, request):
        if not feature_enabled('workflows') and request.method not in ('GET', 'OPTIONS', 'DELETE'):
            raise LicenseForbids(_('Your license does not allow use of workflows.'))
        return super(WorkflowsEnforcementMixin, self).check_permissions(request)


class UnifiedJobDeletionMixin(object):
    '''
    Special handling when deleting a running unified job object.
    '''
    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        if not request.user.can_access(self.model, 'delete', obj):
            raise PermissionDenied()
        try:
            if obj.unified_job_node.workflow_job.status in ACTIVE_STATES:
                raise PermissionDenied(detail=_('Cannot delete job resource when associated workflow job is running.'))
        except self.model.unified_job_node.RelatedObjectDoesNotExist:
            pass
        if obj.status in ACTIVE_STATES:
            raise PermissionDenied(detail=_("Cannot delete running job resource."))
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EnforceParentRelationshipMixin(object):
    '''
    Useful when you have a self-refering ManyToManyRelationship.
    * Tower uses a shallow (2-deep only) url pattern. For example:

    When an object hangs off of a parent object you would have the url of the
    form /api/v1/parent_model/34/child_model. If you then wanted a child of the
    child model you would NOT do /api/v1/parent_model/34/child_model/87/child_child_model
    Instead, you would access the child_child_model via /api/v1/child_child_model/87/
    and you would create child_child_model's off of /api/v1/child_model/87/child_child_model_set
    Now, when creating child_child_model related to child_model you still want to
    link child_child_model to parent_model. That's what this class is for
    '''
    enforce_parent_relationship = ''

    def update_raw_data(self, data):
        data.pop(self.enforce_parent_relationship, None)
        return super(EnforceParentRelationshipMixin, self).update_raw_data(data)

    def create(self, request, *args, **kwargs):
        # Inject parent group inventory ID into new group data.
        data = request.data
        # HACK: Make request data mutable.
        if getattr(data, '_mutable', None) is False:
            data._mutable = True
        data[self.enforce_parent_relationship] = getattr(self.get_parent_object(), '%s_id' % self.enforce_parent_relationship)
        return super(EnforceParentRelationshipMixin, self).create(request, *args, **kwargs)


class OrganizationCountsMixin(object):

    def get_serializer_context(self, *args, **kwargs):
        full_context = super(OrganizationCountsMixin, self).get_serializer_context(*args, **kwargs)

        if self.request is None:
            return full_context

        db_results = {}
        org_qs = self.model.accessible_objects(self.request.user, 'read_role')
        org_id_list = org_qs.values('id')
        if len(org_id_list) == 0:
            if self.request.method == 'POST':
                full_context['related_field_counts'] = {}
            return full_context

        inv_qs = Inventory.accessible_objects(self.request.user, 'read_role')
        project_qs = Project.accessible_objects(self.request.user, 'read_role')

        # Produce counts of Foreign Key relationships
        db_results['inventories'] = inv_qs\
            .values('organization').annotate(Count('organization')).order_by('organization')

        db_results['teams'] = Team.accessible_objects(
            self.request.user, 'read_role').values('organization').annotate(
            Count('organization')).order_by('organization')

        JT_project_reference = 'project__organization'
        JT_inventory_reference = 'inventory__organization'
        db_results['job_templates_project'] = JobTemplate.accessible_objects(
            self.request.user, 'read_role').exclude(
            project__organization=F(JT_inventory_reference)).values(JT_project_reference).annotate(
            Count(JT_project_reference)).order_by(JT_project_reference)

        db_results['job_templates_inventory'] = JobTemplate.accessible_objects(
            self.request.user, 'read_role').values(JT_inventory_reference).annotate(
            Count(JT_inventory_reference)).order_by(JT_inventory_reference)

        db_results['projects'] = project_qs\
            .values('organization').annotate(Count('organization')).order_by('organization')

        # Other members and admins of organization are always viewable
        db_results['users'] = org_qs.annotate(
            users=Count('member_role__members', distinct=True),
            admins=Count('admin_role__members', distinct=True)
        ).values('id', 'users', 'admins')

        count_context = {}
        for org in org_id_list:
            org_id = org['id']
            count_context[org_id] = {
                'inventories': 0, 'teams': 0, 'users': 0, 'job_templates': 0,
                'admins': 0, 'projects': 0}

        for res, count_qs in db_results.items():
            if res == 'job_templates_project':
                org_reference = JT_project_reference
            elif res == 'job_templates_inventory':
                org_reference = JT_inventory_reference
            elif res == 'users':
                org_reference = 'id'
            else:
                org_reference = 'organization'
            for entry in count_qs:
                org_id = entry[org_reference]
                if org_id in count_context:
                    if res == 'users':
                        count_context[org_id]['admins'] = entry['admins']
                        count_context[org_id]['users'] = entry['users']
                        continue
                    count_context[org_id][res] = entry['%s__count' % org_reference]

        # Combine the counts for job templates by project and inventory
        for org in org_id_list:
            org_id = org['id']
            count_context[org_id]['job_templates'] = 0
            for related_path in ['job_templates_project', 'job_templates_inventory']:
                if related_path in count_context[org_id]:
                    count_context[org_id]['job_templates'] += count_context[org_id].pop(related_path)

        full_context['related_field_counts'] = count_context

        return full_context


class CredentialViewMixin(object):

    @property
    def related_search_fields(self):
        ret = super(CredentialViewMixin, self).related_search_fields
        if get_request_version(self.request) == 1 and 'credential_type__search' in ret:
            ret.remove('credential_type__search')
        return ret


class ControlledByScmMixin(object):
    '''
    Special method to reset SCM inventory commit hash
    if anything that it manages changes.
    '''

    def _reset_inv_src_rev(self, obj):
        if self.request.method in SAFE_METHODS or not obj:
            return
        project_following_sources = obj.inventory_sources.filter(
            update_on_project_update=True, source='scm')
        if project_following_sources:
            # Allow inventory changes unrelated to variables
            if self.model == Inventory and (
                    not self.request or not self.request.data or
                    parse_yaml_or_json(self.request.data.get('variables', '')) == parse_yaml_or_json(obj.variables)):
                return
            project_following_sources.update(scm_last_revision='')

    def get_object(self):
        obj = super(ControlledByScmMixin, self).get_object()
        self._reset_inv_src_rev(obj)
        return obj

    def get_parent_object(self):
        obj = super(ControlledByScmMixin, self).get_parent_object()
        self._reset_inv_src_rev(obj)
        return obj


# Copyright (c) 2018 Red Hat, Inc.
# All Rights Reserved.

import dateutil
import logging

from django.db.models import Count
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from rest_framework.permissions import SAFE_METHODS
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import status

from awx.main.constants import ACTIVE_STATES
from awx.main.utils import (
    get_object_or_400,
    parse_yaml_or_json,
)
from awx.main.models.ha import (
    Instance,
    InstanceGroup,
)
from awx.main.models.organization import Team
from awx.main.models.projects import Project
from awx.main.models.inventory import Inventory
from awx.main.models.jobs import JobTemplate
from awx.api.exceptions import ActiveJobConflict

logger = logging.getLogger('awx.api.views.mixin')


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
        # Still allow deletion of new status, because these can be manually created
        if obj.status in ACTIVE_STATES and obj.status != 'new':
            raise PermissionDenied(detail=_("Cannot delete running job resource."))
        elif not obj.event_processing_finished:
            # Prohibit deletion if job events are still coming in
            if obj.finished and now() < obj.finished + dateutil.relativedelta.relativedelta(minutes=1):
                # less than 1 minute has passed since job finished and events are not in
                return Response({"error": _("Job has not finished processing events.")},
                                status=status.HTTP_400_BAD_REQUEST)
            else:
                # if it has been > 1 minute, events are probably lost
                logger.warning('Allowing deletion of {} through the API without all events '
                               'processed.'.format(obj.log_format))
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class InstanceGroupMembershipMixin(object):
    '''
    This mixin overloads attach/detach so that it calls InstanceGroup.save(),
    triggering a background recalculation of policy-based instance group
    membership.
    '''
    def attach(self, request, *args, **kwargs):
        response = super(InstanceGroupMembershipMixin, self).attach(request, *args, **kwargs)
        sub_id, res = self.attach_validate(request)
        if status.is_success(response.status_code):
            if self.parent_model is Instance:
                ig_obj = get_object_or_400(self.model, pk=sub_id)
                inst_name = ig_obj.hostname
            else:
                inst_name = get_object_or_400(self.model, pk=sub_id).hostname
            with transaction.atomic():
                ig_qs = InstanceGroup.objects.select_for_update()
                if self.parent_model is Instance:
                    ig_obj = get_object_or_400(ig_qs, pk=sub_id)
                else:
                    # similar to get_parent_object, but selected for update
                    parent_filter = {
                        self.lookup_field: self.kwargs.get(self.lookup_field, None),
                    }
                    ig_obj = get_object_or_404(ig_qs, **parent_filter)
                if inst_name not in ig_obj.policy_instance_list:
                    ig_obj.policy_instance_list.append(inst_name)
                    ig_obj.save(update_fields=['policy_instance_list'])
        return response

    def is_valid_relation(self, parent, sub, created=False):
        if sub.is_isolated():
            return {'error': _('Isolated instances may not be added or removed from instances groups via the API.')}
        if self.parent_model is InstanceGroup:
            ig_obj = self.get_parent_object()
            if ig_obj.controller_id is not None:
                return {'error': _('Isolated instance group membership may not be managed via the API.')}
        return None

    def unattach_validate(self, request):
        (sub_id, res) = super(InstanceGroupMembershipMixin, self).unattach_validate(request)
        if res:
            return (sub_id, res)
        sub = get_object_or_400(self.model, pk=sub_id)
        attach_errors = self.is_valid_relation(None, sub)
        if attach_errors:
            return (sub_id, Response(attach_errors, status=status.HTTP_400_BAD_REQUEST))
        return (sub_id, res)

    def unattach(self, request, *args, **kwargs):
        response = super(InstanceGroupMembershipMixin, self).unattach(request, *args, **kwargs)
        if status.is_success(response.status_code):
            sub_id = request.data.get('id', None)
            if self.parent_model is Instance:
                inst_name = self.get_parent_object().hostname
            else:
                inst_name = get_object_or_400(self.model, pk=sub_id).hostname
            with transaction.atomic():
                ig_qs = InstanceGroup.objects.select_for_update()
                if self.parent_model is Instance:
                    ig_obj = get_object_or_400(ig_qs, pk=sub_id)
                else:
                    # similar to get_parent_object, but selected for update
                    parent_filter = {
                        self.lookup_field: self.kwargs.get(self.lookup_field, None),
                    }
                    ig_obj = get_object_or_404(ig_qs, **parent_filter)
                if inst_name in ig_obj.policy_instance_list:
                    ig_obj.policy_instance_list.pop(ig_obj.policy_instance_list.index(inst_name))
                    ig_obj.save(update_fields=['policy_instance_list'])
        return response


class RelatedJobsPreventDeleteMixin(object):
    def perform_destroy(self, obj):
        self.check_related_active_jobs(obj)
        return super(RelatedJobsPreventDeleteMixin, self).perform_destroy(obj)

    def check_related_active_jobs(self, obj):
        active_jobs = obj.get_active_jobs()
        if len(active_jobs) > 0:
            raise ActiveJobConflict(active_jobs)
        time_cutoff = now() - dateutil.relativedelta.relativedelta(minutes=1)
        recent_jobs = obj._get_related_jobs().filter(finished__gte = time_cutoff)
        for unified_job in recent_jobs.get_real_instances():
            if not unified_job.event_processing_finished:
                raise PermissionDenied(_(
                    'Related job {} is still processing events.'
                ).format(unified_job.log_format))


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
        jt_qs = JobTemplate.accessible_objects(self.request.user, 'read_role')

        # Produce counts of Foreign Key relationships
        db_results['inventories'] = inv_qs.values('organization').annotate(Count('organization')).order_by('organization')

        db_results['teams'] = Team.accessible_objects(
            self.request.user, 'read_role').values('organization').annotate(
            Count('organization')).order_by('organization')

        db_results['job_templates'] = jt_qs.values('organization').annotate(Count('organization')).order_by('organization')

        db_results['projects'] = project_qs.values('organization').annotate(Count('organization')).order_by('organization')

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
            if res == 'users':
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

        full_context['related_field_counts'] = count_context

        return full_context


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


class NoTruncateMixin(object):
    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.query_params.get('no_truncate'):
            context.update(no_truncate=True)
        return context

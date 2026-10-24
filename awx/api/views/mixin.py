# Copyright (c) 2018 Red Hat, Inc.
# All Rights Reserved.

import dateutil
import logging

from django.db.models import Count, Q, TextField
from django.db.models.functions import Cast
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import status

from awx.main.constants import ACTIVE_STATES
from ansible_base.rbac.models import RoleDefinition, RoleUserAssignment
from awx.main.models import Organization
from awx.main.utils import get_object_or_400
from awx.main.models.ha import Instance, InstanceGroup, schedule_policy_task
from awx.main.models.organization import Team
from awx.main.models.projects import Project
from awx.main.models.inventory import Inventory
from awx.main.models.jobs import JobTemplate
from awx.api.exceptions import ActiveJobConflict

logger = logging.getLogger('awx.api.views.mixin')


class UnifiedJobDeletionMixin(object):
    """
    Special handling when deleting a running unified job object.
    """

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
                return Response({"error": _("Job has not finished processing events.")}, status=status.HTTP_400_BAD_REQUEST)
            else:
                # if it has been > 1 minute, events are probably lost
                logger.warning('Allowing deletion of {} through the API without all events processed.'.format(obj.log_format))

        # Manually cascade delete events if unpartitioned job
        if obj.has_unpartitioned_events:
            obj.get_event_queryset().delete()

        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrganizationInstanceGroupMembershipMixin(object):
    """
    This mixin overloads attach/detach so that it calls Organization.save(),
    to ensure instance group updates are persisted
    """

    def unattach(self, request, *args, **kwargs):
        with transaction.atomic():
            organization_queryset = Organization.objects.select_for_update()
            organization = organization_queryset.get(pk=self.get_parent_object().id)
            response = super(OrganizationInstanceGroupMembershipMixin, self).unattach(request, *args, **kwargs)
            organization.save()
            return response


class InstanceGroupMembershipMixin(object):
    """
    This mixin overloads attach/detach so that it calls InstanceGroup.save(),
    triggering a background recalculation of policy-based instance group
    membership.
    """

    def attach(self, request, *args, **kwargs):
        response = super(InstanceGroupMembershipMixin, self).attach(request, *args, **kwargs)
        if status.is_success(response.status_code):
            sub_id = request.data.get('id', None)
            if self.parent_model is Instance:
                inst_name = self.get_parent_object().hostname
            else:
                inst_name = get_object_or_400(self.model, pk=sub_id).hostname
            with transaction.atomic():
                instance_groups_queryset = InstanceGroup.objects.select_for_update()
                if self.parent_model is Instance:
                    ig_obj = get_object_or_400(instance_groups_queryset, pk=sub_id)
                else:
                    # similar to get_parent_object, but selected for update
                    parent_filter = {self.lookup_field: self.kwargs.get(self.lookup_field, None)}
                    ig_obj = get_object_or_404(instance_groups_queryset, **parent_filter)
                if inst_name not in ig_obj.policy_instance_list:
                    ig_obj.policy_instance_list.append(inst_name)
                    ig_obj.save(update_fields=['policy_instance_list'])
        return response

    def unattach(self, request, *args, **kwargs):
        response = super(InstanceGroupMembershipMixin, self).unattach(request, *args, **kwargs)
        if status.is_success(response.status_code):
            sub_id = request.data.get('id', None)
            if self.parent_model is Instance:
                inst_name = self.get_parent_object().hostname
            else:
                inst_name = get_object_or_400(self.model, pk=sub_id).hostname
            with transaction.atomic():
                instance_groups_queryset = InstanceGroup.objects.select_for_update()
                if self.parent_model is Instance:
                    ig_obj = get_object_or_400(instance_groups_queryset, pk=sub_id)
                else:
                    # similar to get_parent_object, but selected for update
                    parent_filter = {self.lookup_field: self.kwargs.get(self.lookup_field, None)}
                    ig_obj = get_object_or_404(instance_groups_queryset, **parent_filter)
                if inst_name in ig_obj.policy_instance_list:
                    ig_obj.policy_instance_list.pop(ig_obj.policy_instance_list.index(inst_name))
                    ig_obj.save(update_fields=['policy_instance_list'])

            # sometimes removing an instance has a non-obvious consequence
            # this is almost always true if policy_instance_percentage or _minimum is non-zero
            # after removing a single instance, the other memberships need to be re-balanced
            schedule_policy_task()
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
        recent_jobs = obj._get_related_jobs().filter(finished__gte=time_cutoff)
        for unified_job in recent_jobs.get_real_instances():
            if not unified_job.event_processing_finished:
                raise PermissionDenied(_('Related job {} is still processing events.').format(unified_job.log_format))


class OrganizationCountsMixin(object):
    def get_serializer_context(self, *args, **kwargs):
        full_context = super(OrganizationCountsMixin, self).get_serializer_context(*args, **kwargs)

        if self.request is None:
            return full_context

        db_results = {}
        org_qs = self.model.access_qs(self.request.user, 'view')
        org_id_list = org_qs.values('id')
        if len(org_id_list) == 0:
            if self.request.method == 'POST':
                full_context['related_field_counts'] = {}
            return full_context

        inv_qs = Inventory.access_qs(self.request.user, 'view')
        project_qs = Project.access_qs(self.request.user, 'view')
        jt_qs = JobTemplate.access_qs(self.request.user, 'view')

        # Produce counts of Foreign Key relationships
        db_results['inventories'] = inv_qs.values('organization').annotate(Count('organization')).order_by('organization')

        db_results['teams'] = Team.access_qs(self.request.user, 'view').values('organization').annotate(Count('organization')).order_by('organization')

        db_results['job_templates'] = jt_qs.values('organization').annotate(Count('organization')).order_by('organization')

        db_results['projects'] = project_qs.values('organization').annotate(Count('organization')).order_by('organization')

        count_context = {}
        for org in org_id_list:
            org_id = org['id']
            count_context[org_id] = {'inventories': 0, 'teams': 0, 'users': 0, 'job_templates': 0, 'admins': 0, 'projects': 0}

        for res, count_qs in db_results.items():
            for entry in count_qs:
                org_id = entry['organization']
                if org_id in count_context:
                    count_context[org_id][res] = entry['organization__count']

        member_rd = RoleDefinition.objects.filter(name='Organization Member').first()
        admin_rd = RoleDefinition.objects.filter(name='Organization Admin').first()

        if member_rd and admin_rd:
            user_admin_counts = (
                RoleUserAssignment.objects.filter(
                    role_definition__in=[member_rd, admin_rd],
                    object_id__in=org_qs.annotate(text_pk=Cast('pk', TextField())).values('text_pk'),
                )
                .values('object_id')
                .annotate(
                    users=Count('pk', filter=Q(role_definition=member_rd)),
                    admins=Count('pk', filter=Q(role_definition=admin_rd)),
                )
            )
            for entry in user_admin_counts:
                org_id = int(entry['object_id'])
                if org_id in count_context:
                    count_context[org_id]['users'] = entry['users']
                    count_context[org_id]['admins'] = entry['admins']

        full_context['related_field_counts'] = count_context

        return full_context


class NoTruncateMixin(object):
    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.query_params.get('no_truncate'):
            context.update(no_truncate=True)
        return context


class UnifiedJobExcludeMixin(object):
    # Reserve the name 'exclude' so we can use it as a query param. Otherwise, the rest-filters backend
    # would treat it as a model field lookup.
    rest_filters_reserved_names = ('exclude',)

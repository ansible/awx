# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

# Django
from django.db import models
from django.utils.translation import gettext_lazy as _

# AWX
from awx.api.versioning import reverse
from awx.main.models.base import CommonModelNameNotUnique
from awx.main.models.unified_jobs import UnifiedJobTemplate, UnifiedJob
from awx.main.models.inventory import Inventory
from awx.main.models.schedules import Schedule
from awx.main.models.workflow import WorkflowJobTemplateNode, WorkflowJobNode

__all__ = ('Label',)


class Label(CommonModelNameNotUnique):
    """
    Generic Tag. Designed for tagging Job Templates, but expandable to other models.
    """

    class Meta:
        app_label = 'main'
        unique_together = (("name", "organization"),)
        ordering = ('organization', 'name')

    organization = models.ForeignKey(
        'Organization',
        related_name='labels',
        help_text=_('Organization this label belongs to.'),
        on_delete=models.CASCADE,
    )

    def get_absolute_url(self, request=None):
        return reverse('api:label_detail', kwargs={'pk': self.pk}, request=request)

    def is_detached(self):
        return Label.objects.filter(
            id=self.id,
            unifiedjob_labels__isnull=True,
            unifiedjobtemplate_labels__isnull=True,
            inventory_labels__isnull=True,
            schedule_labels__isnull=True,
            workflowjobtemplatenode_labels__isnull=True,
            workflowjobnode_labels__isnull=True,
        ).exists()

    def is_candidate_for_detach(self):
        count = UnifiedJob.objects.filter(labels__in=[self.id]).count()  # Both Jobs and WFJobs
        count += UnifiedJobTemplate.objects.filter(labels__in=[self.id]).count()  # Both JTs and WFJT
        count += Inventory.objects.filter(labels__in=[self.id]).count()
        count += Schedule.objects.filter(labels__in=[self.id]).count()
        count += WorkflowJobTemplateNode.objects.filter(labels__in=[self.id]).count()
        count += WorkflowJobNode.objects.filter(labels__in=[self.id]).count()
        return (count - 1) == 0

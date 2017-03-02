# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

# Django
from django.db import models
from django.utils.translation import ugettext_lazy as _

# AWX
from awx.api.versioning import reverse
from awx.main.models.base import CommonModelNameNotUnique
from awx.main.models.unified_jobs import UnifiedJobTemplate, UnifiedJob

__all__ = ('Label', )


class Label(CommonModelNameNotUnique):
    '''
    Generic Tag. Designed for tagging Job Templates, but expandable to other models.
    '''

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

    @staticmethod
    def get_orphaned_labels():
        return \
            Label.objects.filter(
                organization=None,
                unifiedjobtemplate_labels__isnull=True
            )

    def is_detached(self):
        return bool(
            Label.objects.filter(
                id=self.id,
                unifiedjob_labels__isnull=True,
                unifiedjobtemplate_labels__isnull=True
            ).count())

    def is_candidate_for_detach(self):
        c1 = UnifiedJob.objects.filter(labels__in=[self.id]).count()
        c2 = UnifiedJobTemplate.objects.filter(labels__in=[self.id]).count()
        if (c1 + c2 - 1) == 0:
            return True
        else:
            return False

# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

# Django
from django.db import models
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

# AWX
from awx.main.models.base import CommonModelNameNotUnique

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
        blank=True,
        null=True,
        default=None,
        help_text=_('Organization this label belongs to.'),
        on_delete=models.SET_NULL,
    )

    def get_absolute_url(self):
        return reverse('api:label_detail', args=(self.pk,))

    @staticmethod
    def get_orphaned_labels():
        return \
            Label.objects.filter(
                organization=None,
                jobtemplate_labels__isnull=True
            )


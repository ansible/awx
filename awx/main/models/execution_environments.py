from django.db import models
from django.utils.translation import ugettext_lazy as _

from awx.main.models.base import PrimordialModel


__all__ = ['ExecutionEnvironment']


class ExecutionEnvironment(PrimordialModel):
    class Meta:
        unique_together = ('organization', 'image')
        ordering = (models.F('organization_id').asc(nulls_first=True), 'image')

    organization = models.ForeignKey(
        'Organization',
        null=True,
        default=None,
        blank=True,
        on_delete=models.CASCADE,
        related_name='%(class)ss',
        help_text=_('The organization used to determine access to this execution environment.'),
    )
    image = models.CharField(
        max_length=1024,
        verbose_name=_('image location'),
        help_text=_("The registry location where the container is stored."),
    )
    managed_by_tower = models.BooleanField(default=False, editable=False)
    credential = models.ForeignKey(
        'Credential',
        related_name='%(class)ss',
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    )

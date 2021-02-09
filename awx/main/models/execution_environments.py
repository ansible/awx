from django.db import models
from django.utils.translation import ugettext_lazy as _

from awx.api.versioning import reverse
from awx.main.models.base import CommonModel


__all__ = ['ExecutionEnvironment']


class ExecutionEnvironment(CommonModel):
    class Meta:
        ordering = ('-created',)

    PULL_CHOICES = [
        ('always', _("Always pull container before running.")),
        ('missing', _("No pull option has been selected.")),
        ('never', _("Never pull container before running."))
    ]

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
    pull = models.CharField(
        max_length=1024,
        choices=PULL_CHOICES,
        default='missing',
        help_text=_('Pull image before running?'),
    )

    def get_absolute_url(self, request=None):
        return reverse('api:execution_environment_detail', kwargs={'pk': self.pk}, request=request)

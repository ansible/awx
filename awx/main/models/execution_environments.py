from django.db import models
from django.utils.translation import ugettext_lazy as _

from awx.api.versioning import reverse
from awx.main.models.base import CommonModel
from awx.main.utils import copy_model_by_class, copy_m2m_relationships


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
        max_length=16,
        choices=PULL_CHOICES,
        blank=True,
        default='',
        help_text=_('Pull image before running?'),
    )

    def copy_execution_environment(self):
        '''
        Returns saved object, including related fields.
        Create a copy of this unified job template.
        '''
        execution_environment_class = self.__class__
        fields = (f.name for f in self.Meta.fields)
        execution_environment_copy = copy_model_by_class(self, execution_environment_class, fields, {})

        time_now = now()
        execution_environment_copy.name = execution_environment_copy.name.split('@', 1)[0] + ' @ ' + time_now.strftime('%I:%M:%S %p')

        execution_environment_copy.save()
        copy_m2m_relationships(self, execution_environment_copy, fields)
        return execution_environment_copy

    def get_absolute_url(self, request=None):
        return reverse('api:execution_environment_detail', kwargs={'pk': self.pk}, request=request)

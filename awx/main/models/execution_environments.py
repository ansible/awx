from django.db import models
from django.utils.translation import gettext_lazy as _

from rest_framework.exceptions import ValidationError

from awx.api.versioning import reverse
from awx.main.models.base import CommonModel
from awx.main.validators import validate_container_image_name


__all__ = ['ExecutionEnvironment']


class ExecutionEnvironment(CommonModel):
    class Meta:
        ordering = ('-created',)
        # Remove view permission, as a temporary solution, defer to organization read permission
        default_permissions = ('add', 'change', 'delete')

    PULL_CHOICES = [
        ('always', _("Always pull container before running.")),
        ('missing', _("Only pull the image if not present before running.")),
        ('never', _("Never pull container before running.")),
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
        help_text=_("The full image location, including the container registry, image name, and version tag."),
        validators=[validate_container_image_name],
    )
    managed = models.BooleanField(default=False, editable=False)
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

    def get_absolute_url(self, request=None):
        return reverse('api:execution_environment_detail', kwargs={'pk': self.pk}, request=request)

    def validate_role_assignment(self, actor, role_definition, **kwargs):
        from awx.main.models.credential import check_resource_server_for_user_in_organization

        if self.managed:
            raise ValidationError({'object_id': _('Can not assign object roles to managed Execution Environments')})
        if self.organization_id is None:
            raise ValidationError({'object_id': _('Can not assign object roles to global Execution Environments')})

        if actor._meta.model_name == 'user':
            if actor.has_obj_perm(self.organization, 'view'):
                return

            requesting_user = kwargs.get('requesting_user', None)
            if check_resource_server_for_user_in_organization(actor, self.organization, requesting_user):
                return

            raise ValidationError({'user': _('User must have view permission to Execution Environment organization')})

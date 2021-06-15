from base64 import b64encode
import json
import os
import stat
import tempfile

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

    def get_absolute_url(self, request=None):
        return reverse('api:execution_environment_detail', kwargs={'pk': self.pk}, request=request)

    def build_authfile(self):
        if not self.credential:
            return None
        if not self.credential.has_inputs(field_names=('host', 'username', 'password')):
            raise RuntimeError('Please recheck that your host, username, and password fields are all filled.')

        authfile = tempfile.NamedTemporaryFile(delete=False)
        os.chmod(authfile.name, stat.S_IRUSR | stat.S_IWUSR)
        host = self.credential.get_input('host')
        username = self.credential.get_input('username')
        password = self.credential.get_input('password')
        token = f"{username}:{password}"
        auth_data = {'auths': {host: {'auth': b64encode(token.encode('utf-8')).decode('utf-8')}}}
        authfile.write(json.dumps(auth_data, indent=4).encode('utf-8'))
        authfile.close()
        return authfile.name

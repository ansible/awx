# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python

# Django
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
# Tower
from awx.main.models.base import CreatedModifiedModel

class TowerSettings(CreatedModifiedModel):

    class Meta:
        app_label = 'main'

    SETTINGS_TYPE_CHOICES = [
        ('string', _("String")),
        ('int', _('Integer')),
        ('float', _('Decimal')),
        ('json', _('JSON')),
        ('bool', _('Boolean')),
        ('password', _('Password')),
        ('list', _('List'))
    ]

    key = models.CharField(
        max_length=255,
        unique=True
    )
    description = models.TextField()
    category = models.CharField(max_length=128)
    value = models.TextField()
    value_type = models.CharField(
        max_length=12,
        choices=SETTINGS_TYPE_CHOICES
    )
    user = models.ForeignKey(
        'auth.User',
        related_name='settings',
        default=None,
        null=True,
        editable=False,
    )

    @property
    def value_converted(self):
        if self.value_type == 'json':
            converted_type = json.loads(self.value)
        elif self.value_type == 'password':
            converted_type = self.value
        elif self.value_type == 'list':
            converted_type = [x.strip() for x in self.value.split(',')]
        elif self.value_type == 'bool':
            converted_type = self.value in [True, "true", "True", 1, "1", "yes"]
        elif self.value_type == 'string':
            converted_type = self.value
        else:
            t = __builtins__[self.value_type]
            converted_type = t(self.value)
        return converted_type

# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python

# Django
from django.conf import settings
from django.db import models

# Tower
from awx.main.models.base import CreatedModifiedModel

class TowerSettings(CreatedModifiedModel):

    SETTINGS_TYPE_CHOICES = [
        ('string', "String"),
        ('int', 'Integer'),
        ('float', 'Decimal'),
        ('json', 'JSON'),
        ('password', 'Password'),
        ('list', 'List')
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


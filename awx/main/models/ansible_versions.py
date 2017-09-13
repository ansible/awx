# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved.

# Django
from django.db import models
from django.utils.translation import ugettext_lazy as _

# AWX
from awx.main.models.base import * #noqa

class AnsibleVersions(CommonModel):
    '''
    random thing
    '''

    ansible_cmd = models.TextField(
        blank=True,
        default='',
        help_text=_('Full path to ansible command.'),
    )


    ansible_playbook = models.TextField(
        blank=True,
        default='',
        help_text=_('Full path to ansible command.'),
    )

    ansible_vault = models.TextField(
        blank=True,
        default='',
        help_text=_('Full path to ansible command.'),
    )

    ansible_doc = models.TextField(
        blank=True,
        default='',
        help_text=_('Full path to ansible command.'),
    )


    ansible_pull = models.TextField(
        blank=True,
        default='',
        help_text=_('Full path to ansible command.'),
    )

    ansible_galaxy = models.TextField(
        blank=True,
        default='',
        help_text=_('Full path to ansible command.'),
        )


# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

import re

from django.utils.translation import ugettext_lazy as _

__all__ = [
    'CLOUD_PROVIDERS', 'SCHEDULEABLE_PROVIDERS', 'PRIVILEGE_ESCALATION_METHODS',
    'ANSI_SGR_PATTERN', 'CAN_CANCEL', 'ACTIVE_STATES'
]


CLOUD_PROVIDERS = ('azure_rm', 'ec2', 'gce', 'vmware', 'openstack', 'rhv', 'satellite6', 'cloudforms', 'tower')
SCHEDULEABLE_PROVIDERS = CLOUD_PROVIDERS + ('custom', 'scm',)
PRIVILEGE_ESCALATION_METHODS = [
    ('sudo', _('Sudo')), ('su', _('Su')), ('pbrun', _('Pbrun')), ('pfexec', _('Pfexec')),
    ('dzdo', _('DZDO')), ('pmrun', _('Pmrun')), ('runas', _('Runas')),
    ('enable', _('Enable')), ('doas', _('Doas')),
]
CHOICES_PRIVILEGE_ESCALATION_METHODS = [('', _('None'))] + PRIVILEGE_ESCALATION_METHODS
ANSI_SGR_PATTERN = re.compile(r'\x1b\[[0-9;]*m')
CAN_CANCEL = ('new', 'pending', 'waiting', 'running')
ACTIVE_STATES = CAN_CANCEL
TOKEN_CENSOR = '************'

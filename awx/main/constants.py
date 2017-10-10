# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

import re

from django.utils.translation import ugettext_lazy as _

CLOUD_PROVIDERS = ('azure_rm', 'ec2', 'gce', 'vmware', 'openstack', 'satellite6', 'cloudforms')
SCHEDULEABLE_PROVIDERS = CLOUD_PROVIDERS + ('custom', 'scm',)
PRIVILEGE_ESCALATION_METHODS = [ ('sudo', _('Sudo')), ('su', _('Su')), ('pbrun', _('Pbrun')), ('pfexec', _('Pfexec')), ('dzdo', _('DZDO')), ('pmrun', _('Pmrun')), ('runas', _('Runas'))]
ANSI_SGR_PATTERN = re.compile(r'\x1b\[[0-9;]*m')

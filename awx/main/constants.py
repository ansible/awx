# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

import re

from django.utils.translation import ugettext_lazy as _

__all__ = [
    'CLOUD_PROVIDERS', 'SCHEDULEABLE_PROVIDERS', 'PRIVILEGE_ESCALATION_METHODS',
    'ANSI_SGR_PATTERN', 'CAN_CANCEL', 'ACTIVE_STATES', 'STANDARD_INVENTORY_UPDATE_ENV'
]

CLOUD_PROVIDERS = ('azure_rm', 'ec2', 'gce', 'vmware', 'openstack', 'rhv', 'satellite6', 'tower')
SCHEDULEABLE_PROVIDERS = CLOUD_PROVIDERS + ('custom', 'scm',)
PRIVILEGE_ESCALATION_METHODS = [
    ('sudo', _('Sudo')), ('su', _('Su')), ('pbrun', _('Pbrun')), ('pfexec', _('Pfexec')),
    ('dzdo', _('DZDO')), ('pmrun', _('Pmrun')), ('runas', _('Runas')),
    ('enable', _('Enable')), ('doas', _('Doas')), ('ksu', _('Ksu')),
    ('machinectl', _('Machinectl')), ('sesu', _('Sesu')),
]
CHOICES_PRIVILEGE_ESCALATION_METHODS = [('', _('None'))] + PRIVILEGE_ESCALATION_METHODS
ANSI_SGR_PATTERN = re.compile(r'\x1b\[[0-9;]*m')
STANDARD_INVENTORY_UPDATE_ENV = {
    # Failure to parse inventory should always be fatal
    'ANSIBLE_INVENTORY_UNPARSED_FAILED': 'True',
    # Always use the --export option for ansible-inventory
    'ANSIBLE_INVENTORY_EXPORT': 'True',
    # Redirecting output to stderr allows JSON parsing to still work with -vvv
    'ANSIBLE_VERBOSE_TO_STDERR': 'True'
}
CAN_CANCEL = ('new', 'pending', 'waiting', 'running')
ACTIVE_STATES = CAN_CANCEL
CENSOR_VALUE = '************'
ENV_BLOCKLIST = frozenset((
    'VIRTUAL_ENV', 'PATH', 'PYTHONPATH', 'PROOT_TMP_DIR', 'JOB_ID',
    'INVENTORY_ID', 'INVENTORY_SOURCE_ID', 'INVENTORY_UPDATE_ID',
    'AD_HOC_COMMAND_ID', 'REST_API_URL', 'REST_API_TOKEN', 'MAX_EVENT_RES',
    'CALLBACK_QUEUE', 'CALLBACK_CONNECTION', 'CACHE',
    'JOB_CALLBACK_DEBUG', 'INVENTORY_HOSTVARS',
    'AWX_HOST', 'PROJECT_REVISION', 'SUPERVISOR_WEB_CONFIG_PATH'
))

# loggers that may be called in process of emitting a log
LOGGER_BLOCKLIST = (
    'awx.main.utils.handlers',
    'awx.main.utils.formatters',
    'awx.main.utils.filters',
    'awx.main.utils.encryption',
    'awx.main.utils.log',
    # loggers that may be called getting logging settings
    'awx.conf'
)

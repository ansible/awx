# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

import re

from django.utils.translation import gettext_lazy as _

__all__ = [
    'CLOUD_PROVIDERS',
    'PRIVILEGE_ESCALATION_METHODS',
    'ANSI_SGR_PATTERN',
    'CAN_CANCEL',
    'ACTIVE_STATES',
    'STANDARD_INVENTORY_UPDATE_ENV',
]

CLOUD_PROVIDERS = ('azure_rm', 'ec2', 'gce', 'vmware', 'openstack', 'rhv', 'satellite6', 'controller', 'insights')
PRIVILEGE_ESCALATION_METHODS = [
    ('sudo', _('Sudo')),
    ('su', _('Su')),
    ('pbrun', _('Pbrun')),
    ('pfexec', _('Pfexec')),
    ('dzdo', _('DZDO')),
    ('pmrun', _('Pmrun')),
    ('runas', _('Runas')),
    ('enable', _('Enable')),
    ('doas', _('Doas')),
    ('ksu', _('Ksu')),
    ('machinectl', _('Machinectl')),
    ('sesu', _('Sesu')),
]
CHOICES_PRIVILEGE_ESCALATION_METHODS = [('', _('None'))] + PRIVILEGE_ESCALATION_METHODS
ANSI_SGR_PATTERN = re.compile(r'\x1b\[[0-9;]*m')
STANDARD_INVENTORY_UPDATE_ENV = {
    # Failure to parse inventory should always be fatal
    'ANSIBLE_INVENTORY_UNPARSED_FAILED': 'True',
    # Always use the --export option for ansible-inventory
    'ANSIBLE_INVENTORY_EXPORT': 'True',
    # Redirecting output to stderr allows JSON parsing to still work with -vvv
    'ANSIBLE_VERBOSE_TO_STDERR': 'True',
}
CAN_CANCEL = ('new', 'pending', 'waiting', 'running')
ACTIVE_STATES = CAN_CANCEL
MINIMAL_EVENTS = set(['playbook_on_play_start', 'playbook_on_task_start', 'playbook_on_stats', 'EOF'])
CENSOR_VALUE = '************'
ENV_BLOCKLIST = frozenset(
    (
        'VIRTUAL_ENV',
        'PATH',
        'PYTHONPATH',
        'JOB_ID',
        'INVENTORY_ID',
        'INVENTORY_SOURCE_ID',
        'INVENTORY_UPDATE_ID',
        'AD_HOC_COMMAND_ID',
        'REST_API_URL',
        'REST_API_TOKEN',
        'MAX_EVENT_RES',
        'CALLBACK_QUEUE',
        'CALLBACK_CONNECTION',
        'CACHE',
        'JOB_CALLBACK_DEBUG',
        'INVENTORY_HOSTVARS',
        'AWX_HOST',
        'PROJECT_REVISION',
        'SUPERVISOR_WEB_CONFIG_PATH',
    )
)

# loggers that may be called in process of emitting a log
LOGGER_BLOCKLIST = (
    'awx.main.utils.handlers',
    'awx.main.utils.formatters',
    'awx.main.utils.filters',
    'awx.main.utils.encryption',
    'awx.main.utils.log',
    # loggers that may be called getting logging settings
    'awx.conf',
)

# Reported version for node seen in receptor mesh but for which capacity check
# failed or is in progress
RECEPTOR_PENDING = 'ansible-runner-???'

# Naming pattern for AWX jobs in /tmp folder, like /tmp/awx_42_xiwm
# also update awxkit.api.pages.unified_jobs if changed
JOB_FOLDER_PREFIX = 'awx_%s_'

# :z option tells Podman that two containers share the volume content with r/w
# :O option tells Podman to mount the directory from the host as a temporary storage using the overlay file system.
# :ro or :rw option to mount a volume in read-only or read-write mode, respectively. By default, the volumes are mounted read-write.
# see podman-run manpage for further details
# /HOST-DIR:/CONTAINER-DIR:OPTIONS
CONTAINER_VOLUMES_MOUNT_TYPES = ['z', 'O', 'ro', 'rw']
MAX_ISOLATED_PATH_COLON_DELIMITER = 2

SURVEY_TYPE_MAPPING = {'text': str, 'textarea': str, 'password': str, 'multiplechoice': str, 'multiselect': str, 'integer': int, 'float': (float, int)}

JOB_VARIABLE_PREFIXES = [
    'awx',
    'tower',
]

# Note, the \u001b[... are ansi color codes. We don't currenly import any of the python modules which define the codes.
# Importing a library just for this message seemed like overkill
ANSIBLE_RUNNER_NEEDS_UPDATE_MESSAGE = (
    '\u001b[31m \u001b[1m This can be caused if the version of ansible-runner in your execution environment is out of date.\u001b[0m'
)

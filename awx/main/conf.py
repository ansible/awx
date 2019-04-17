# Python
import json
import logging
import os

# Django
from django.utils.translation import ugettext_lazy as _

# Django REST Framework
from rest_framework import serializers

# Tower
from awx.conf import fields, register, register_validate

logger = logging.getLogger('awx.main.conf')

register(
    'ACTIVITY_STREAM_ENABLED',
    field_class=fields.BooleanField,
    label=_('Enable Activity Stream'),
    help_text=_('Enable capturing activity for the activity stream.'),
    category=_('System'),
    category_slug='system',
)

register(
    'ACTIVITY_STREAM_ENABLED_FOR_INVENTORY_SYNC',
    field_class=fields.BooleanField,
    label=_('Enable Activity Stream for Inventory Sync'),
    help_text=_('Enable capturing activity for the activity stream when running inventory sync.'),
    category=_('System'),
    category_slug='system',
)

register(
    'ORG_ADMINS_CAN_SEE_ALL_USERS',
    field_class=fields.BooleanField,
    label=_('All Users Visible to Organization Admins'),
    help_text=_('Controls whether any Organization Admin can view all users and teams, '
                'even those not associated with their Organization.'),
    category=_('System'),
    category_slug='system',
)

register(
    'MANAGE_ORGANIZATION_AUTH',
    field_class=fields.BooleanField,
    label=_('Organization Admins Can Manage Users and Teams'),
    help_text=_('Controls whether any Organization Admin has the privileges to create and manage users and teams. '
                'You may want to disable this ability if you are using an LDAP or SAML integration.'),
    category=_('System'),
    category_slug='system',
)

register(
    'TOWER_ADMIN_ALERTS',
    field_class=fields.BooleanField,
    label=_('Enable Administrator Alerts'),
    help_text=_('Email Admin users for system events that may require attention.'),
    category=_('System'),
    category_slug='system',
)

register(
    'TOWER_URL_BASE',
    field_class=fields.URLField,
    schemes=('http', 'https'),
    allow_plain_hostname=True,  # Allow hostname only without TLD.
    label=_('Base URL of the Tower host'),
    help_text=_('This setting is used by services like notifications to render '
                'a valid url to the Tower host.'),
    category=_('System'),
    category_slug='system',
)

register(
    'REMOTE_HOST_HEADERS',
    field_class=fields.StringListField,
    label=_('Remote Host Headers'),
    help_text=_('HTTP headers and meta keys to search to determine remote host '
                'name or IP. Add additional items to this list, such as '
                '"HTTP_X_FORWARDED_FOR", if behind a reverse proxy. '
                'See the "Proxy Support" section of the Adminstrator guide for '
                'more details.'),
    category=_('System'),
    category_slug='system',
)

register(
    'PROXY_IP_WHITELIST',
    field_class=fields.StringListField,
    label=_('Proxy IP Whitelist'),
    help_text=_("If Tower is behind a reverse proxy/load balancer, use this setting "
                "to whitelist the proxy IP addresses from which Tower should trust "
                "custom REMOTE_HOST_HEADERS header values. "
                "If this setting is an empty list (the default), the headers specified by "
                "REMOTE_HOST_HEADERS will be trusted unconditionally')"),
    category=_('System'),
    category_slug='system',
)


def _load_default_license_from_file():
    try:
        license_file = os.environ.get('AWX_LICENSE_FILE', '/etc/tower/license')
        if os.path.exists(license_file):
            license_data = json.load(open(license_file))
            logger.debug('Read license data from "%s".', license_file)
            return license_data
    except Exception:
        logger.warning('Could not read license from "%s".', license_file, exc_info=True)
    return {}


register(
    'LICENSE',
    field_class=fields.DictField,
    default=_load_default_license_from_file,
    label=_('License'),
    help_text=_('The license controls which features and functionality are '
                'enabled. Use /api/v1/config/ to update or change '
                'the license.'),
    category=_('System'),
    category_slug='system',
)

register(
    'INSTALL_UUID',
    field_class=fields.CharField,
    label=_('Unique identifier for an AWX/Tower installation'),
    category=_('System'),
    category_slug='system',
    read_only=True,
)

register(
    'CUSTOM_VENV_PATHS',
    field_class=fields.StringListPathField,
    label=_('Custom virtual environment paths'),
    help_text=_('Paths where Tower will look for custom virtual environments '
                '(in addition to /var/lib/awx/venv/). Enter one path per line.'),
    category=_('System'),
    category_slug='system',
    default=[],
)

register(
    'AD_HOC_COMMANDS',
    field_class=fields.StringListField,
    label=_('Ansible Modules Allowed for Ad Hoc Jobs'),
    help_text=_('List of modules allowed to be used by ad-hoc jobs.'),
    category=_('Jobs'),
    category_slug='jobs',
    required=False,
)

register(
    'ALLOW_JINJA_IN_EXTRA_VARS',
    field_class=fields.ChoiceField,
    choices=[
        ('always', _('Always')),
        ('never', _('Never')),
        ('template', _('Only On Job Template Definitions')),
    ],
    required=True,
    label=_('When can extra variables contain Jinja templates?'),
    help_text=_(
        'Ansible allows variable substitution via the Jinja2 templating '
        'language for --extra-vars. This poses a potential security '
        'risk where Tower users with the ability to specify extra vars at job '
        'launch time can use Jinja2 templates to run arbitrary Python.  It is '
        'recommended that this value be set to "template" or "never".'
    ),
    category=_('Jobs'),
    category_slug='jobs',
)

register(
    'AWX_PROOT_ENABLED',
    field_class=fields.BooleanField,
    label=_('Enable job isolation'),
    help_text=_('Isolates an Ansible job from protected parts of the system to prevent exposing sensitive information.'),
    category=_('Jobs'),
    category_slug='jobs',
)

register(
    'AWX_PROOT_BASE_PATH',
    field_class=fields.CharField,
    label=_('Job execution path'),
    help_text=_('The directory in which Tower will create new temporary '
                'directories for job execution and isolation '
                '(such as credential files and custom inventory scripts).'),
    category=_('Jobs'),
    category_slug='jobs',
)

register(
    'AWX_PROOT_HIDE_PATHS',
    field_class=fields.StringListField,
    required=False,
    label=_('Paths to hide from isolated jobs'),
    help_text=_('Additional paths to hide from isolated processes. Enter one path per line.'),
    category=_('Jobs'),
    category_slug='jobs',
)

register(
    'AWX_PROOT_SHOW_PATHS',
    field_class=fields.StringListField,
    required=False,
    label=_('Paths to expose to isolated jobs'),
    help_text=_('Whitelist of paths that would otherwise be hidden to expose to isolated jobs. Enter one path per line.'),
    category=_('Jobs'),
    category_slug='jobs',
)

register(
    'AWX_ISOLATED_VERBOSITY',
    field_class=fields.IntegerField,
    min_value=0,
    max_value=5,
    label=_('Verbosity level for isolated node management tasks'),
    help_text=_('This can be raised to aid in debugging connection issues for isolated task execution'),
    category=_('Jobs'),
    category_slug='jobs',
    default=0
)

register(
    'AWX_ISOLATED_CHECK_INTERVAL',
    field_class=fields.IntegerField,
    min_value=0,
    label=_('Isolated status check interval'),
    help_text=_('The number of seconds to sleep between status checks for jobs running on isolated instances.'),
    category=_('Jobs'),
    category_slug='jobs',
)

register(
    'AWX_ISOLATED_LAUNCH_TIMEOUT',
    field_class=fields.IntegerField,
    min_value=0,
    label=_('Isolated launch timeout'),
    help_text=_('The timeout (in seconds) for launching jobs on isolated instances.  '
                'This includes the time needed to copy source control files (playbooks) to the isolated instance.'),
    category=_('Jobs'),
    category_slug='jobs',
)

register(
    'AWX_ISOLATED_CONNECTION_TIMEOUT',
    field_class=fields.IntegerField,
    min_value=0,
    default=10,
    label=_('Isolated connection timeout'),
    help_text=_('Ansible SSH connection timeout (in seconds) to use when communicating with isolated instances. '
                'Value should be substantially greater than expected network latency.'),
    category=_('Jobs'),
    category_slug='jobs',
)

register(
    'AWX_ISOLATED_KEY_GENERATION',
    field_class=fields.BooleanField,
    default=True,
    label=_('Generate RSA keys for isolated instances'),
    help_text=_('If set, a random RSA key will be generated and distributed to '
                'isolated instances.  To disable this behavior and manage authentication '
                'for isolated instances outside of Tower, disable this setting.'),  # noqa
    category=_('Jobs'),
    category_slug='jobs',
)

register(
    'AWX_ISOLATED_PRIVATE_KEY',
    field_class=fields.CharField,
    default='',
    allow_blank=True,
    encrypted=True,
    read_only=True,
    label=_('The RSA private key for SSH traffic to isolated instances'),
    help_text=_('The RSA private key for SSH traffic to isolated instances'),  # noqa
    category=_('Jobs'),
    category_slug='jobs',
)

register(
    'AWX_ISOLATED_PUBLIC_KEY',
    field_class=fields.CharField,
    default='',
    allow_blank=True,
    read_only=True,
    label=_('The RSA public key for SSH traffic to isolated instances'),
    help_text=_('The RSA public key for SSH traffic to isolated instances'),  # noqa
    category=_('Jobs'),
    category_slug='jobs',
)

register(
    'AWX_TASK_ENV',
    field_class=fields.KeyValueField,
    default={},
    label=_('Extra Environment Variables'),
    help_text=_('Additional environment variables set for playbook runs, inventory updates, project updates, and notification sending.'),
    category=_('Jobs'),
    category_slug='jobs',
    placeholder={'HTTP_PROXY': 'myproxy.local:8080'},
)

register(
    'INSIGHTS_TRACKING_STATE',
    field_class=fields.BooleanField,
    default=False,
    label=_('Gather data for Automation Insights'),
    help_text=_('Enables Tower to gather data on automation and send it to Red Hat Insights.'),
    category=_('System'),
    category_slug='system',
)

register(
    'AWX_ROLES_ENABLED',
    field_class=fields.BooleanField,
    default=True,
    label=_('Enable Role Download'),
    help_text=_('Allows roles to be dynamically downloaded from a requirements.yml file for SCM projects.'),
    category=_('Jobs'),
    category_slug='jobs',
)

register(
    'STDOUT_MAX_BYTES_DISPLAY',
    field_class=fields.IntegerField,
    min_value=0,
    label=_('Standard Output Maximum Display Size'),
    help_text=_('Maximum Size of Standard Output in bytes to display before requiring the output be downloaded.'),
    category=_('Jobs'),
    category_slug='jobs',
)

register(
    'EVENT_STDOUT_MAX_BYTES_DISPLAY',
    field_class=fields.IntegerField,
    min_value=0,
    label=_('Job Event Standard Output Maximum Display Size'),
    help_text=_(
        u'Maximum Size of Standard Output in bytes to display for a single job or ad hoc command event. `stdout` will end with `\u2026` when truncated.'),
    category=_('Jobs'),
    category_slug='jobs',
)

register(
    'SCHEDULE_MAX_JOBS',
    field_class=fields.IntegerField,
    min_value=1,
    label=_('Maximum Scheduled Jobs'),
    help_text=_('Maximum number of the same job template that can be waiting to run when launching from a schedule before no more are created.'),
    category=_('Jobs'),
    category_slug='jobs',
)

register(
    'AWX_ANSIBLE_CALLBACK_PLUGINS',
    field_class=fields.StringListField,
    required=False,
    label=_('Ansible Callback Plugins'),
    help_text=_('List of paths to search for extra callback plugins to be used when running jobs. Enter one path per line.'),
    category=_('Jobs'),
    category_slug='jobs',
)

register(
    'DEFAULT_JOB_TIMEOUT',
    field_class=fields.IntegerField,
    min_value=0,
    default=0,
    label=_('Default Job Timeout'),
    help_text=_('Maximum time in seconds to allow jobs to run. Use value of 0 to indicate that no '
                'timeout should be imposed. A timeout set on an individual job template will override this.'),
    category=_('Jobs'),
    category_slug='jobs',
)

register(
    'DEFAULT_INVENTORY_UPDATE_TIMEOUT',
    field_class=fields.IntegerField,
    min_value=0,
    default=0,
    label=_('Default Inventory Update Timeout'),
    help_text=_('Maximum time in seconds to allow inventory updates to run. Use value of 0 to indicate that no '
                'timeout should be imposed. A timeout set on an individual inventory source will override this.'),
    category=_('Jobs'),
    category_slug='jobs',
)

register(
    'DEFAULT_PROJECT_UPDATE_TIMEOUT',
    field_class=fields.IntegerField,
    min_value=0,
    default=0,
    label=_('Default Project Update Timeout'),
    help_text=_('Maximum time in seconds to allow project updates to run. Use value of 0 to indicate that no '
                'timeout should be imposed. A timeout set on an individual project will override this.'),
    category=_('Jobs'),
    category_slug='jobs',
)

register(
    'ANSIBLE_FACT_CACHE_TIMEOUT',
    field_class=fields.IntegerField,
    min_value=0,
    default=0,
    label=_('Per-Host Ansible Fact Cache Timeout'),
    help_text=_('Maximum time, in seconds, that stored Ansible facts are considered valid since '
                'the last time they were modified. Only valid, non-stale, facts will be accessible by '
                'a playbook. Note, this does not influence the deletion of ansible_facts from the database. '
                'Use a value of 0 to indicate that no timeout should be imposed.'),
    category=_('Jobs'),
    category_slug='jobs',
)

register(
    'LOG_AGGREGATOR_HOST',
    field_class=fields.CharField,
    allow_null=True,
    default=None,
    label=_('Logging Aggregator'),
    help_text=_('Hostname/IP where external logs will be sent to.'),
    category=_('Logging'),
    category_slug='logging',
)
register(
    'LOG_AGGREGATOR_PORT',
    field_class=fields.IntegerField,
    allow_null=True,
    default=None,
    label=_('Logging Aggregator Port'),
    help_text=_('Port on Logging Aggregator to send logs to (if required and not'
                ' provided in Logging Aggregator).'),
    category=_('Logging'),
    category_slug='logging',
    required=False
)
register(
    'LOG_AGGREGATOR_TYPE',
    field_class=fields.ChoiceField,
    choices=['logstash', 'splunk', 'loggly', 'sumologic', 'other'],
    allow_null=True,
    default=None,
    label=_('Logging Aggregator Type'),
    help_text=_('Format messages for the chosen log aggregator.'),
    category=_('Logging'),
    category_slug='logging',
)
register(
    'LOG_AGGREGATOR_USERNAME',
    field_class=fields.CharField,
    allow_blank=True,
    default='',
    label=_('Logging Aggregator Username'),
    help_text=_('Username for external log aggregator (if required).'),
    category=_('Logging'),
    category_slug='logging',
    required=False,
)
register(
    'LOG_AGGREGATOR_PASSWORD',
    field_class=fields.CharField,
    allow_blank=True,
    default='',
    encrypted=True,
    label=_('Logging Aggregator Password/Token'),
    help_text=_('Password or authentication token for external log aggregator (if required).'),
    category=_('Logging'),
    category_slug='logging',
    required=False,
)
register(
    'LOG_AGGREGATOR_LOGGERS',
    field_class=fields.StringListField,
    default=['awx', 'activity_stream', 'job_events', 'system_tracking'],
    label=_('Loggers Sending Data to Log Aggregator Form'),
    help_text=_('List of loggers that will send HTTP logs to the collector, these can '
                'include any or all of: \n'
                'awx - service logs\n'
                'activity_stream - activity stream records\n'
                'job_events - callback data from Ansible job events\n'
                'system_tracking - facts gathered from scan jobs.'),
    category=_('Logging'),
    category_slug='logging',
)
register(
    'LOG_AGGREGATOR_INDIVIDUAL_FACTS',
    field_class=fields.BooleanField,
    default=False,
    label=_('Log System Tracking Facts Individually'),
    help_text=_('If set, system tracking facts will be sent for each package, service, or '
                'other item found in a scan, allowing for greater search query granularity. '
                'If unset, facts will be sent as a single dictionary, allowing for greater '
                'efficiency in fact processing.'),
    category=_('Logging'),
    category_slug='logging',
)
register(
    'LOG_AGGREGATOR_ENABLED',
    field_class=fields.BooleanField,
    default=False,
    label=_('Enable External Logging'),
    help_text=_('Enable sending logs to external log aggregator.'),
    category=_('Logging'),
    category_slug='logging',
)
register(
    'LOG_AGGREGATOR_TOWER_UUID',
    field_class=fields.CharField,
    allow_blank=True,
    default='',
    label=_('Cluster-wide Tower unique identifier.'),
    help_text=_('Useful to uniquely identify Tower instances.'),
    category=_('Logging'),
    category_slug='logging',
)
register(
    'LOG_AGGREGATOR_PROTOCOL',
    field_class=fields.ChoiceField,
    choices=[('https', 'HTTPS/HTTP'), ('tcp', 'TCP'), ('udp', 'UDP')],
    default='https',
    label=_('Logging Aggregator Protocol'),
    help_text=_('Protocol used to communicate with log aggregator.  '
                'HTTPS/HTTP assumes HTTPS unless http:// is explicitly used in '
                'the Logging Aggregator hostname.'),
    category=_('Logging'),
    category_slug='logging',
)
register(
    'LOG_AGGREGATOR_TCP_TIMEOUT',
    field_class=fields.IntegerField,
    default=5,
    label=_('TCP Connection Timeout'),
    help_text=_('Number of seconds for a TCP connection to external log '
                'aggregator to timeout. Applies to HTTPS and TCP log '
                'aggregator protocols.'),
    category=_('Logging'),
    category_slug='logging',
)
register(
    'LOG_AGGREGATOR_VERIFY_CERT',
    field_class=fields.BooleanField,
    default=True,
    label=_('Enable/disable HTTPS certificate verification'),
    help_text=_('Flag to control enable/disable of certificate verification'
                ' when LOG_AGGREGATOR_PROTOCOL is "https". If enabled, Tower\'s'
                ' log handler will verify certificate sent by external log aggregator'
                ' before establishing connection.'),
    category=_('Logging'),
    category_slug='logging',
)
register(
    'LOG_AGGREGATOR_LEVEL',
    field_class=fields.ChoiceField,
    choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
    default='WARNING',
    label=_('Logging Aggregator Level Threshold'),
    help_text=_('Level threshold used by log handler. Severities from lowest to highest'
                ' are DEBUG, INFO, WARNING, ERROR, CRITICAL. Messages less severe '
                'than the threshold will be ignored by log handler. (messages under category '
                'awx.anlytics ignore this setting)'),
    category=_('Logging'),
    category_slug='logging',
)


def logging_validate(serializer, attrs):
    if not serializer.instance or \
            not hasattr(serializer.instance, 'LOG_AGGREGATOR_HOST') or \
            not hasattr(serializer.instance, 'LOG_AGGREGATOR_TYPE'):
        return attrs
    errors = []
    if attrs.get('LOG_AGGREGATOR_ENABLED', False):
        if not serializer.instance.LOG_AGGREGATOR_HOST and not attrs.get('LOG_AGGREGATOR_HOST', None) or\
                serializer.instance.LOG_AGGREGATOR_HOST and not attrs.get('LOG_AGGREGATOR_HOST', True):
            errors.append('Cannot enable log aggregator without providing host.')
        if not serializer.instance.LOG_AGGREGATOR_TYPE and not attrs.get('LOG_AGGREGATOR_TYPE', None) or\
                serializer.instance.LOG_AGGREGATOR_TYPE and not attrs.get('LOG_AGGREGATOR_TYPE', True):
            errors.append('Cannot enable log aggregator without providing type.')
    if errors:
        raise serializers.ValidationError(_('\n'.join(errors)))
    return attrs


register_validate('logging', logging_validate)

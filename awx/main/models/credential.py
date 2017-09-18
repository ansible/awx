# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.
from collections import OrderedDict
import functools
import json
import operator
import os
import stat
import tempfile

# Jinja2
from jinja2 import Template

# Django
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils.encoding import force_text

# AWX
from awx.api.versioning import reverse
from awx.main.constants import PRIVILEGE_ESCALATION_METHODS
from awx.main.fields import (ImplicitRoleField, CredentialInputField,
                             CredentialTypeInputField,
                             CredentialTypeInjectorField)
from awx.main.utils import decrypt_field
from awx.main.validators import validate_ssh_private_key
from awx.main.models.base import * # noqa
from awx.main.models.mixins import ResourceMixin
from awx.main.models.rbac import (
    ROLE_SINGLETON_SYSTEM_ADMINISTRATOR,
    ROLE_SINGLETON_SYSTEM_AUDITOR,
)
from awx.main.utils import encrypt_field

__all__ = ['Credential', 'CredentialType', 'V1Credential']


class V1Credential(object):

    #
    # API v1 backwards compat; as long as we continue to support the
    # /api/v1/credentials/ endpoint, we'll keep these definitions around.
    # The credential serializers are smart enough to detect the request
    # version and use *these* fields for constructing the serializer if the URL
    # starts with /api/v1/
    #
    PASSWORD_FIELDS = ('password', 'security_token', 'ssh_key_data',
                       'ssh_key_unlock', 'become_password',
                       'vault_password', 'secret', 'authorize_password')
    KIND_CHOICES = [
        ('ssh', 'Machine'),
        ('net', 'Network'),
        ('scm', 'Source Control'),
        ('aws', 'Amazon Web Services'),
        ('vmware', 'VMware vCenter'),
        ('satellite6', 'Red Hat Satellite 6'),
        ('cloudforms', 'Red Hat CloudForms'),
        ('gce', 'Google Compute Engine'),
        ('azure_rm', 'Microsoft Azure Resource Manager'),
        ('openstack', 'OpenStack'),
        ('insights', 'Insights'),
    ]
    FIELDS = {
        'kind': models.CharField(
            max_length=32,
            choices=[
                (kind[0], _(kind[1]))
                for kind in KIND_CHOICES
            ],
            default='ssh',
        ),
        'cloud': models.BooleanField(
            default=False,
            editable=False,
        ),
        'host': models.CharField(
            blank=True,
            default='',
            max_length=1024,
            verbose_name=_('Host'),
            help_text=_('The hostname or IP address to use.'),
        ),
        'username': models.CharField(
            blank=True,
            default='',
            max_length=1024,
            verbose_name=_('Username'),
            help_text=_('Username for this credential.'),
        ),
        'password': models.CharField(
            blank=True,
            default='',
            max_length=1024,
            verbose_name=_('Password'),
            help_text=_('Password for this credential (or "ASK" to prompt the '
                        'user for machine credentials).'),
        ),
        'security_token': models.CharField(
            blank=True,
            default='',
            max_length=1024,
            verbose_name=_('Security Token'),
            help_text=_('Security Token for this credential'),
        ),
        'project': models.CharField(
            blank=True,
            default='',
            max_length=100,
            verbose_name=_('Project'),
            help_text=_('The identifier for the project.'),
        ),
        'domain': models.CharField(
            blank=True,
            default='',
            max_length=100,
            verbose_name=_('Domain'),
            help_text=_('The identifier for the domain.'),
        ),
        'ssh_key_data': models.TextField(
            blank=True,
            default='',
            verbose_name=_('SSH private key'),
            help_text=_('RSA or DSA private key to be used instead of password.'),
        ),
        'ssh_key_unlock': models.CharField(
            max_length=1024,
            blank=True,
            default='',
            verbose_name=_('SSH key unlock'),
            help_text=_('Passphrase to unlock SSH private key if encrypted (or '
                        '"ASK" to prompt the user for machine credentials).'),
        ),
        'become_method': models.CharField(
            max_length=32,
            blank=True,
            default='',
            choices=[('', _('None'))] + PRIVILEGE_ESCALATION_METHODS,
            help_text=_('Privilege escalation method.')
        ),
        'become_username': models.CharField(
            max_length=1024,
            blank=True,
            default='',
            help_text=_('Privilege escalation username.'),
        ),
        'become_password': models.CharField(
            max_length=1024,
            blank=True,
            default='',
            help_text=_('Password for privilege escalation method.')
        ),
        'vault_password': models.CharField(
            max_length=1024,
            blank=True,
            default='',
            help_text=_('Vault password (or "ASK" to prompt the user).'),
        ),
        'authorize': models.BooleanField(
            default=False,
            help_text=_('Whether to use the authorize mechanism.'),
        ),
        'authorize_password': models.CharField(
            max_length=1024,
            blank=True,
            default='',
            help_text=_('Password used by the authorize mechanism.'),
        ),
        'client': models.CharField(
            max_length=128,
            blank=True,
            default='',
            help_text=_('Client Id or Application Id for the credential'),
        ),
        'secret': models.CharField(
            max_length=1024,
            blank=True,
            default='',
            help_text=_('Secret Token for this credential'),
        ),
        'subscription': models.CharField(
            max_length=1024,
            blank=True,
            default='',
            help_text=_('Subscription identifier for this credential'),
        ),
        'tenant': models.CharField(
            max_length=1024,
            blank=True,
            default='',
            help_text=_('Tenant identifier for this credential'),
        )
    }



class Credential(PasswordFieldsModel, CommonModelNameNotUnique, ResourceMixin):
    '''
    A credential contains information about how to talk to a remote resource
    Usually this is a SSH key location, and possibly an unlock password.
    If used with sudo, a sudo password should be set if required.
    '''

    class Meta:
        app_label = 'main'
        ordering = ('name',)
        unique_together = (('organization', 'name', 'credential_type'))

    PASSWORD_FIELDS = ['inputs']

    credential_type = models.ForeignKey(
        'CredentialType',
        related_name='credentials',
        null=False,
        help_text=_('Specify the type of credential you want to create. Refer '
                    'to the Ansible Tower documentation for details on each type.')
    )
    organization = models.ForeignKey(
        'Organization',
        null=True,
        default=None,
        blank=True,
        on_delete=models.CASCADE,
        related_name='credentials',
    )
    inputs = CredentialInputField(
        blank=True,
        default={},
        help_text=_('Enter inputs using either JSON or YAML syntax. Use the '
                    'radio button to toggle between the two. Refer to the '
                    'Ansible Tower documentation for example syntax.')
    )
    admin_role = ImplicitRoleField(
        parent_role=[
            'singleton:' + ROLE_SINGLETON_SYSTEM_ADMINISTRATOR,
            'organization.admin_role',
        ],
    )
    use_role = ImplicitRoleField(
        parent_role=[
            'admin_role',
        ]
    )
    read_role = ImplicitRoleField(parent_role=[
        'singleton:' + ROLE_SINGLETON_SYSTEM_AUDITOR,
        'organization.auditor_role',
        'use_role',
        'admin_role',
    ])

    def __getattr__(self, item):
        if item in V1Credential.FIELDS:
            return self.inputs.get(item, V1Credential.FIELDS[item].default)
        elif item in self.inputs:
            return self.inputs[item]
        raise AttributeError(item)

    def __setattr__(self, item, value):
        if item in V1Credential.FIELDS and item in self.credential_type.defined_fields:
            if value:
                self.inputs[item] = value
            elif item in self.inputs:
                del self.inputs[item]
            return
        super(Credential, self).__setattr__(item, value)

    @property
    def kind(self):
        # TODO 3.3: remove the need for this helper property by removing its
        # usage throughout the codebase
        type_ = self.credential_type
        if type_.kind != 'cloud':
            return type_.kind
        for field in V1Credential.KIND_CHOICES:
            kind, name = field
            if name == type_.name:
                return kind

    @property
    def cloud(self):
        return self.credential_type.kind == 'cloud'

    def get_absolute_url(self, request=None):
        return reverse('api:credential_detail', kwargs={'pk': self.pk}, request=request)

    #
    # TODO: the SSH-related properties below are largely used for validation
    # and for determining passwords necessary for job/ad-hoc launch
    #
    # These are SSH-specific; should we move them elsewhere?
    #
    @property
    def needs_ssh_password(self):
        return self.credential_type.kind == 'ssh' and self.password == 'ASK'

    @property
    def has_encrypted_ssh_key_data(self):
        if self.pk:
            ssh_key_data = decrypt_field(self, 'ssh_key_data')
        else:
            ssh_key_data = self.ssh_key_data
        try:
            pem_objects = validate_ssh_private_key(ssh_key_data)
            for pem_object in pem_objects:
                if pem_object.get('key_enc', False):
                    return True
        except ValidationError:
            pass
        return False

    @property
    def needs_ssh_key_unlock(self):
        if self.credential_type.kind == 'ssh' and self.ssh_key_unlock in ('ASK', ''):
            return self.has_encrypted_ssh_key_data
        return False

    @property
    def needs_become_password(self):
        return self.credential_type.kind == 'ssh' and self.become_password == 'ASK'

    @property
    def needs_vault_password(self):
        return self.credential_type.kind == 'vault' and self.vault_password == 'ASK'

    @property
    def passwords_needed(self):
        needed = []
        for field in ('ssh_password', 'become_password', 'ssh_key_unlock', 'vault_password'):
            if getattr(self, 'needs_%s' % field):
                needed.append(field)
        return needed

    def _password_field_allows_ask(self, field):
        return field in self.credential_type.askable_fields

    def save(self, *args, **kwargs):
        self.PASSWORD_FIELDS = self.credential_type.secret_fields

        if self.pk:
            cred_before = Credential.objects.get(pk=self.pk)
            inputs_before = cred_before.inputs
            # Look up the currently persisted value so that we can replace
            # $encrypted$ with the actual DB-backed value
            for field in self.PASSWORD_FIELDS:
                if self.inputs.get(field) == '$encrypted$':
                    self.inputs[field] = inputs_before[field]

        super(Credential, self).save(*args, **kwargs)

    def encrypt_field(self, field, ask):
        encrypted = encrypt_field(self, field, ask=ask)
        if encrypted:
            self.inputs[field] = encrypted
        elif field in self.inputs:
            del self.inputs[field]

    def mark_field_for_save(self, update_fields, field):
        if field in self.credential_type.secret_fields:
            # If we've encrypted a v1 field, we actually want to persist
            # self.inputs
            field = 'inputs'
        super(Credential, self).mark_field_for_save(update_fields, field)

    def display_inputs(self):
        field_val = self.inputs.copy()
        for k, v in field_val.items():
            if force_text(v).startswith('$encrypted$'):
                field_val[k] = '$encrypted$'
        return field_val


class CredentialType(CommonModelNameNotUnique):
    '''
    A reusable schema for a credential.

    Used to define a named credential type with fields (e.g., an API key) and
    output injectors (i.e., an environment variable that uses the API key).
    '''

    defaults = OrderedDict()

    ENV_BLACKLIST = set((
        'VIRTUAL_ENV', 'PATH', 'PYTHONPATH', 'PROOT_TMP_DIR', 'JOB_ID',
        'INVENTORY_ID', 'INVENTORY_SOURCE_ID', 'INVENTORY_UPDATE_ID',
        'AD_HOC_COMMAND_ID', 'REST_API_URL', 'REST_API_TOKEN', 'TOWER_HOST',
        'AWX_HOST', 'MAX_EVENT_RES', 'CALLBACK_QUEUE', 'CALLBACK_CONNECTION', 'CACHE',
        'JOB_CALLBACK_DEBUG', 'INVENTORY_HOSTVARS', 'FACT_QUEUE',
    ))

    class Meta:
        app_label = 'main'
        ordering = ('kind', 'name')
        unique_together = (('name', 'kind'),)

    KIND_CHOICES = (
        ('ssh', _('Machine')),
        ('vault', _('Vault')),
        ('net', _('Network')),
        ('scm', _('Source Control')),
        ('cloud', _('Cloud')),
        ('insights', _('Insights')),
    )

    kind = models.CharField(
        max_length=32,
        choices=KIND_CHOICES
    )
    managed_by_tower = models.BooleanField(
        default=False,
        editable=False
    )
    inputs = CredentialTypeInputField(
        blank=True,
        default={},
        help_text=_('Enter inputs using either JSON or YAML syntax. Use the '
                    'radio button to toggle between the two. Refer to the '
                    'Ansible Tower documentation for example syntax.')
    )
    injectors = CredentialTypeInjectorField(
        blank=True,
        default={},
        help_text=_('Enter injectors using either JSON or YAML syntax. Use the '
                    'radio button to toggle between the two. Refer to the '
                    'Ansible Tower documentation for example syntax.')
    )

    def get_absolute_url(self, request=None):
        return reverse('api:credential_type_detail', kwargs={'pk': self.pk}, request=request)

    @property
    def unique_by_kind(self):
        return self.kind != 'cloud'

    @property
    def defined_fields(self):
        return [field.get('id') for field in self.inputs.get('fields', [])]

    @property
    def secret_fields(self):
        return [
            field['id'] for field in self.inputs.get('fields', [])
            if field.get('secret', False) is True
        ]

    @property
    def askable_fields(self):
        return [
            field['id'] for field in self.inputs.get('fields', [])
            if field.get('ask_at_runtime', False) is True
        ]

    def default_for_field(self, field_id):
        for field in self.inputs.get('fields', []):
            if field['id'] == field_id:
                if 'choices' in field:
                    return field['choices'][0]
                return {'string': '', 'boolean': False}[field['type']]

    @classmethod
    def default(cls, f):
        func = functools.partial(f, cls)
        cls.defaults[f.__name__] = func
        return func

    @classmethod
    def setup_tower_managed_defaults(cls, persisted=True):
        for default in cls.defaults.values():
            default_ = default()
            if persisted:
                default_.save()

    @classmethod
    def from_v1_kind(cls, kind, data={}):
        match = None
        kind = kind or 'ssh'
        kind_choices = dict(V1Credential.KIND_CHOICES)
        requirements = {}
        if kind == 'ssh':
            if data.get('vault_password'):
                requirements['kind'] = 'vault'
            else:
                requirements['kind'] = 'ssh'
        elif kind in ('net', 'scm', 'insights'):
            requirements['kind'] = kind
        elif kind in kind_choices:
            requirements.update(dict(
                kind='cloud',
                name=kind_choices[kind]
            ))
        if requirements:
            requirements['managed_by_tower'] = True
            match = cls.objects.filter(**requirements)[:1].get()
        return match

    def inject_credential(self, credential, env, safe_env, args, safe_args, private_data_dir):
        """
        Inject credential data into the environment variables and arguments
        passed to `ansible-playbook`

        :param credential:       a :class:`awx.main.models.Credential` instance
        :param env:              a dictionary of environment variables used in
                                 the `ansible-playbook` call.  This method adds
                                 additional environment variables based on
                                 custom `env` injectors defined on this
                                 CredentialType.
        :param safe_env:         a dictionary of environment variables stored
                                 in the database for the job run
                                 (`UnifiedJob.job_env`); secret values should
                                 be stripped
        :param args:             a list of arguments passed to
                                 `ansible-playbook` in the style of
                                 `subprocess.call(args)`.  This method appends
                                 additional arguments based on custom
                                 `extra_vars` injectors defined on this
                                 CredentialType.
        :param safe_args:        a list of arguments stored in the database for
                                 the job run (`UnifiedJob.job_args`); secret
                                 values should be stripped
        :param private_data_dir: a temporary directory to store files generated
                                 by `file` injectors (like config files or key
                                 files)
        """
        if not self.injectors:
            return

        class TowerNamespace:
            filename = None

        tower_namespace = TowerNamespace()

        # maintain a normal namespace for building the ansible-playbook arguments (env and args)
        namespace = {'tower': tower_namespace}

        # maintain a sanitized namespace for building the DB-stored arguments (safe_env and safe_args)
        safe_namespace = {'tower': tower_namespace}

        # build a normal namespace with secret values decrypted (for
        # ansible-playbook) and a safe namespace with secret values hidden (for
        # DB storage)
        for field_name, value in credential.inputs.items():

            if type(value) is bool:
                # boolean values can't be secret/encrypted
                safe_namespace[field_name] = namespace[field_name] = value
                continue

            if field_name in self.secret_fields:
                value = decrypt_field(credential, field_name)
                safe_namespace[field_name] = '**********'
            elif len(value):
                safe_namespace[field_name] = value
            if len(value):
                namespace[field_name] = value

        file_tmpl = self.injectors.get('file', {}).get('template')
        if file_tmpl is not None:
            # If a file template is provided, render the file and update the
            # special `tower` template namespace so the filename can be
            # referenced in other injectors
            data = Template(file_tmpl).render(**namespace)
            _, path = tempfile.mkstemp(dir=private_data_dir)
            with open(path, 'w') as f:
                f.write(data)
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
            namespace['tower'].filename = path

        for env_var, tmpl in self.injectors.get('env', {}).items():
            if env_var.startswith('ANSIBLE_') or env_var in self.ENV_BLACKLIST:
                continue
            env[env_var] = Template(tmpl).render(**namespace)
            safe_env[env_var] = Template(tmpl).render(**safe_namespace)

        extra_vars = {}
        safe_extra_vars = {}
        for var_name, tmpl in self.injectors.get('extra_vars', {}).items():
            extra_vars[var_name] = Template(tmpl).render(**namespace)
            safe_extra_vars[var_name] = Template(tmpl).render(**safe_namespace)

        if extra_vars:
            args.extend(['-e', json.dumps(extra_vars)])

        if safe_extra_vars:
            safe_args.extend(['-e', json.dumps(safe_extra_vars)])


@CredentialType.default
def ssh(cls):
    return cls(
        kind='ssh',
        name='Machine',
        managed_by_tower=True,
        inputs={
            'fields': [{
                'id': 'username',
                'label': 'Username',
                'type': 'string'
            }, {
                'id': 'password',
                'label': 'Password',
                'type': 'string',
                'secret': True,
                'ask_at_runtime': True
            }, {
                'id': 'ssh_key_data',
                'label': 'SSH Private Key',
                'type': 'string',
                'format': 'ssh_private_key',
                'secret': True,
                'multiline': True
            }, {
                'id': 'ssh_key_unlock',
                'label': 'Private Key Passphrase',
                'type': 'string',
                'secret': True,
                'ask_at_runtime': True
            }, {
                'id': 'become_method',
                'label': 'Privilege Escalation Method',
                'choices': map(operator.itemgetter(0),
                               V1Credential.FIELDS['become_method'].choices),
                'help_text': ('Specify a method for "become" operations. This is '
                              'equivalent to specifying the --become-method '
                              'Ansible parameter.')
            }, {
                'id': 'become_username',
                'label': 'Privilege Escalation Username',
                'type': 'string',
            }, {
                'id': 'become_password',
                'label': 'Privilege Escalation Password',
                'type': 'string',
                'secret': True,
                'ask_at_runtime': True
            }],
            'dependencies': {
                'ssh_key_unlock': ['ssh_key_data'],
            }
        }
    )


@CredentialType.default
def scm(cls):
    return cls(
        kind='scm',
        name='Source Control',
        managed_by_tower=True,
        inputs={
            'fields': [{
                'id': 'username',
                'label': 'Username',
                'type': 'string'
            }, {
                'id': 'password',
                'label': 'Password',
                'type': 'string',
                'secret': True
            }, {
                'id': 'ssh_key_data',
                'label': 'SCM Private Key',
                'type': 'string',
                'format': 'ssh_private_key',
                'secret': True,
                'multiline': True
            }, {
                'id': 'ssh_key_unlock',
                'label': 'Private Key Passphrase',
                'type': 'string',
                'secret': True
            }],
            'dependencies': {
                'ssh_key_unlock': ['ssh_key_data'],
            }
        }
    )


@CredentialType.default
def vault(cls):
    return cls(
        kind='vault',
        name='Vault',
        managed_by_tower=True,
        inputs={
            'fields': [{
                'id': 'vault_password',
                'label': 'Vault Password',
                'type': 'string',
                'secret': True,
                'ask_at_runtime': True
            }],
            'required': ['vault_password'],
        }
    )


@CredentialType.default
def net(cls):
    return cls(
        kind='net',
        name='Network',
        managed_by_tower=True,
        inputs={
            'fields': [{
                'id': 'username',
                'label': 'Username',
                'type': 'string'
            }, {
                'id': 'password',
                'label': 'Password',
                'type': 'string',
                'secret': True,
            }, {
                'id': 'ssh_key_data',
                'label': 'SSH Private Key',
                'type': 'string',
                'format': 'ssh_private_key',
                'secret': True,
                'multiline': True
            }, {
                'id': 'ssh_key_unlock',
                'label': 'Private Key Passphrase',
                'type': 'string',
                'secret': True,
            }, {
                'id': 'authorize',
                'label': 'Authorize',
                'type': 'boolean',
            }, {
                'id': 'authorize_password',
                'label': 'Authorize Password',
                'type': 'string',
                'secret': True,
            }],
            'dependencies': {
                'ssh_key_unlock': ['ssh_key_data'],
                'authorize_password': ['authorize'],
            },
            'required': ['username'],
        }
    )


@CredentialType.default
def aws(cls):
    return cls(
        kind='cloud',
        name='Amazon Web Services',
        managed_by_tower=True,
        inputs={
            'fields': [{
                'id': 'username',
                'label': 'Access Key',
                'type': 'string'
            }, {
                'id': 'password',
                'label': 'Secret Key',
                'type': 'string',
                'secret': True,
            }, {
                'id': 'security_token',
                'label': 'STS Token',
                'type': 'string',
                'secret': True,
                'help_text': ('Security Token Service (STS) is a web service '
                              'that enables you to request temporary, '
                              'limited-privilege credentials for AWS Identity '
                              'and Access Management (IAM) users.'),
            }],
            'required': ['username', 'password']
        }
    )


@CredentialType.default
def openstack(cls):
    return cls(
        kind='cloud',
        name='OpenStack',
        managed_by_tower=True,
        inputs={
            'fields': [{
                'id': 'username',
                'label': 'Username',
                'type': 'string'
            }, {
                'id': 'password',
                'label': 'Password (API Key)',
                'type': 'string',
                'secret': True,
            }, {
                'id': 'host',
                'label': 'Host (Authentication URL)',
                'type': 'string',
                'help_text': ('The host to authenticate with.  For example, '
                              'https://openstack.business.com/v2.0/')
            }, {
                'id': 'project',
                'label': 'Project (Tenant Name)',
                'type': 'string',
            }, {
                'id': 'domain',
                'label': 'Domain Name',
                'type': 'string',
                'help_text': ('OpenStack domains define administrative boundaries. '
                              'It is only needed for Keystone v3 authentication '
                              'URLs. Refer to Ansible Tower documentation for '
                              'common scenarios.')
            }],
            'required': ['username', 'password', 'host', 'project']
        }
    )


@CredentialType.default
def vmware(cls):
    return cls(
        kind='cloud',
        name='VMware vCenter',
        managed_by_tower=True,
        inputs={
            'fields': [{
                'id': 'host',
                'label': 'VCenter Host',
                'type': 'string',
                'help_text': ('Enter the hostname or IP address that corresponds '
                              'to your VMware vCenter.')
            }, {
                'id': 'username',
                'label': 'Username',
                'type': 'string'
            }, {
                'id': 'password',
                'label': 'Password',
                'type': 'string',
                'secret': True,
            }],
            'required': ['host', 'username', 'password']
        }
    )


@CredentialType.default
def satellite6(cls):
    return cls(
        kind='cloud',
        name='Red Hat Satellite 6',
        managed_by_tower=True,
        inputs={
            'fields': [{
                'id': 'host',
                'label': 'Satellite 6 URL',
                'type': 'string',
                'help_text': ('Enter the URL that corresponds to your Red Hat '
                              'Satellite 6 server. For example, https://satellite.example.org')
            }, {
                'id': 'username',
                'label': 'Username',
                'type': 'string'
            }, {
                'id': 'password',
                'label': 'Password',
                'type': 'string',
                'secret': True,
            }],
            'required': ['host', 'username', 'password'],
        }
    )


@CredentialType.default
def cloudforms(cls):
    return cls(
        kind='cloud',
        name='Red Hat CloudForms',
        managed_by_tower=True,
        inputs={
            'fields': [{
                'id': 'host',
                'label': 'CloudForms URL',
                'type': 'string',
                'help_text': ('Enter the URL for the virtual machine that '
                              'corresponds to your CloudForm instance. '
                              'For example, https://cloudforms.example.org')
            }, {
                'id': 'username',
                'label': 'Username',
                'type': 'string'
            }, {
                'id': 'password',
                'label': 'Password',
                'type': 'string',
                'secret': True,
            }],
            'required': ['host', 'username', 'password'],
        }
    )


@CredentialType.default
def gce(cls):
    return cls(
        kind='cloud',
        name='Google Compute Engine',
        managed_by_tower=True,
        inputs={
            'fields': [{
                'id': 'username',
                'label': 'Service Account Email Address',
                'type': 'string',
                'help_text': ('The email address assigned to the Google Compute '
                              'Engine service account.')
            }, {
                'id': 'project',
                'label': 'Project',
                'type': 'string',
                'help_text': ('The Project ID is the GCE assigned identification. '
                              'It is often constructed as three words or two words '
                              'followed by a three-digit number. Examples: project-id-000 '
                              'and another-project-id')
            }, {
                'id': 'ssh_key_data',
                'label': 'RSA Private Key',
                'type': 'string',
                'format': 'ssh_private_key',
                'secret': True,
                'multiline': True,
                'help_text': ('Paste the contents of the PEM file associated '
                              'with the service account email.')
            }],
            'required': ['username', 'ssh_key_data'],
        }
    )


@CredentialType.default
def azure_rm(cls):
    return cls(
        kind='cloud',
        name='Microsoft Azure Resource Manager',
        managed_by_tower=True,
        inputs={
            'fields': [{
                'id': 'subscription',
                'label': 'Subscription ID',
                'type': 'string',
                'help_text': ('Subscription ID is an Azure construct, which is '
                              'mapped to a username.')
            }, {
                'id': 'username',
                'label': 'Username',
                'type': 'string'
            }, {
                'id': 'password',
                'label': 'Password',
                'type': 'string',
                'secret': True,
            }, {
                'id': 'client',
                'label': 'Client ID',
                'type': 'string'
            }, {
                'id': 'secret',
                'label': 'Client Secret',
                'type': 'string',
                'secret': True,
            }, {
                'id': 'tenant',
                'label': 'Tenant ID',
                'type': 'string'
            }],
            'required': ['subscription'],
        }
    )


@CredentialType.default
def insights(cls):
    return cls(
        kind='insights',
        name='Insights',
        managed_by_tower=True,
        inputs={
            'fields': [{
                'id': 'username',
                'label': 'Username',
                'type': 'string'
            }, {
                'id': 'password',
                'label': 'Password',
                'type': 'string',
                'secret': True
            }],
            'required': ['username', 'password'],
        },
        injectors={
            'extra_vars': {
                "scm_username": "{{username}}",
                "scm_password": "{{password}}",
            },
        },
    )

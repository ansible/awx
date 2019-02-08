# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.
from collections import OrderedDict
import functools
import logging
import os
import re
import stat
import tempfile

# Jinja2
from jinja2 import Template

# Django
from django.db import models
from django.utils.translation import ugettext_lazy as _, ugettext_noop
from django.core.exceptions import ValidationError
from django.utils.encoding import force_text

# AWX
from awx.api.versioning import reverse
from awx.main.fields import (ImplicitRoleField, CredentialInputField,
                             CredentialTypeInputField,
                             CredentialTypeInjectorField)
from awx.main.utils import decrypt_field
from awx.main.utils.safe_yaml import safe_dump
from awx.main.validators import validate_ssh_private_key
from awx.main.models.base import * # noqa
from awx.main.models.mixins import ResourceMixin
from awx.main.models.rbac import (
    ROLE_SINGLETON_SYSTEM_ADMINISTRATOR,
    ROLE_SINGLETON_SYSTEM_AUDITOR,
)
from awx.main.utils import encrypt_field
from . import injectors as builtin_injectors

__all__ = ['Credential', 'CredentialType', 'V1Credential', 'build_safe_env']

logger = logging.getLogger('awx.main.models.credential')

HIDDEN_PASSWORD = '**********'


def build_safe_env(env):
    '''
    Build environment dictionary, hiding potentially sensitive information
    such as passwords or keys.
    '''
    hidden_re = re.compile(r'API|TOKEN|KEY|SECRET|PASS', re.I)
    urlpass_re = re.compile(r'^.*?://[^:]+:(.*?)@.*?$')
    safe_env = dict(env)
    for k, v in safe_env.items():
        if k == 'AWS_ACCESS_KEY_ID':
            continue
        elif k.startswith('ANSIBLE_') and not k.startswith('ANSIBLE_NET'):
            continue
        elif hidden_re.search(k):
            safe_env[k] = HIDDEN_PASSWORD
        elif type(v) == str and urlpass_re.match(v):
            safe_env[k] = urlpass_re.sub(HIDDEN_PASSWORD, v)
    return safe_env


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
        ('rhv', 'Red Hat Virtualization'),
        ('insights', 'Insights'),
        ('tower', 'Ansible Tower'),
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
            'organization.credential_admin_role',
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
        if item != 'inputs':
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
        try:
            ssh_key_data = decrypt_field(self, 'ssh_key_data')
        except AttributeError:
            return False

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
        for field in ('ssh_password', 'become_password', 'ssh_key_unlock'):
            if getattr(self, 'needs_%s' % field):
                needed.append(field)
        if self.needs_vault_password:
            if self.inputs.get('vault_id'):
                needed.append('vault_password.{}'.format(self.inputs.get('vault_id')))
            else:
                needed.append('vault_password')
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
        if field not in self.inputs:
            return None
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

    def unique_hash(self, display=False):
        '''
        Credential exclusivity is not defined solely by the related
        credential type (due to vault), so this produces a hash
        that can be used to evaluate exclusivity
        '''
        if display:
            type_alias = self.credential_type.name
        else:
            type_alias = self.credential_type_id
        if self.kind == 'vault' and self.has_input('vault_id'):
            if display:
                fmt_str = '{} (id={})'
            else:
                fmt_str = '{}_{}'
            return fmt_str.format(type_alias, self.get_input('vault_id'))
        return str(type_alias)

    @staticmethod
    def unique_dict(cred_qs):
        ret = {}
        for cred in cred_qs:
            ret[cred.unique_hash()] = cred
        return ret

    def get_input(self, field_name, **kwargs):
        """
        Get an injectable and decrypted value for an input field.

        Retrieves the value for a given credential input field name. Return
        values for secret input fields are decrypted. If the credential doesn't
        have an input value defined for the given field name, an AttributeError
        is raised unless a default value is provided.

        :param field_name(str):        The name of the input field.
        :param default(optional[str]): A default return value to use.
        """
        if field_name in self.credential_type.secret_fields:
            try:
                return decrypt_field(self, field_name)
            except AttributeError:
                if 'default' in kwargs:
                    return kwargs['default']
                raise AttributeError
        if field_name in self.inputs:
            return self.inputs[field_name]
        if 'default' in kwargs:
            return kwargs['default']
        raise AttributeError(field_name)

    def has_input(self, field_name):
        return field_name in self.inputs and self.inputs[field_name] not in ('', None)


class CredentialType(CommonModelNameNotUnique):
    '''
    A reusable schema for a credential.

    Used to define a named credential type with fields (e.g., an API key) and
    output injectors (i.e., an environment variable that uses the API key).
    '''

    defaults = OrderedDict()

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
        # Page does not exist in API v1
        if request.version == 'v1':
            return reverse('api:credential_type_detail', kwargs={'pk': self.pk})
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
                if CredentialType.objects.filter(name=default_.name, kind=default_.kind).count():
                    continue
                logger.debug(_(
                    "adding %s credential type" % default_.name
                ))
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
            if self.managed_by_tower and credential.kind in dir(builtin_injectors):
                injected_env = {}
                getattr(builtin_injectors, credential.kind)(credential, injected_env, private_data_dir)
                env.update(injected_env)
                safe_env.update(build_safe_env(injected_env))
            return

        class TowerNamespace:
            pass

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

            value = credential.get_input(field_name)

            if field_name in self.secret_fields:
                safe_namespace[field_name] = '**********'
            elif len(value):
                safe_namespace[field_name] = value
            if len(value):
                namespace[field_name] = value

        # default missing boolean fields to False
        for field in self.inputs.get('fields', []):
            if field['type'] == 'boolean' and field['id'] not in credential.inputs.keys():
                namespace[field['id']] = safe_namespace[field['id']] = False

        file_tmpls = self.injectors.get('file', {})
        # If any file templates are provided, render the files and update the
        # special `tower` template namespace so the filename can be
        # referenced in other injectors
        for file_label, file_tmpl in file_tmpls.items():
            data = Template(file_tmpl).render(**namespace)
            _, path = tempfile.mkstemp(dir=private_data_dir)
            with open(path, 'w') as f:
                f.write(data)
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)

            # determine if filename indicates single file or many
            if file_label.find('.') == -1:
                tower_namespace.filename = path
            else:
                if not hasattr(tower_namespace, 'filename'):
                    tower_namespace.filename = TowerNamespace()
                file_label = file_label.split('.')[1]
                setattr(tower_namespace.filename, file_label, path)

        injector_field = self._meta.get_field('injectors')
        for env_var, tmpl in self.injectors.get('env', {}).items():
            try:
                injector_field.validate_env_var_allowed(env_var)
            except ValidationError as e:
                logger.error('Ignoring prohibited env var {}, reason: {}'.format(env_var, e))
                continue
            env[env_var] = Template(tmpl).render(**namespace)
            safe_env[env_var] = Template(tmpl).render(**safe_namespace)

        if 'INVENTORY_UPDATE_ID' not in env:
            # awx-manage inventory_update does not support extra_vars via -e
            extra_vars = {}
            for var_name, tmpl in self.injectors.get('extra_vars', {}).items():
                extra_vars[var_name] = Template(tmpl).render(**namespace)

            def build_extra_vars_file(vars, private_dir):
                handle, path = tempfile.mkstemp(dir = private_dir)
                f = os.fdopen(handle, 'w')
                f.write(safe_dump(vars))
                f.close()
                os.chmod(path, stat.S_IRUSR)
                return path

            path = build_extra_vars_file(extra_vars, private_data_dir)
            if extra_vars:
                args.extend(['-e', '@%s' % path])
                safe_args.extend(['-e', '@%s' % path])


@CredentialType.default
def ssh(cls):
    return cls(
        kind='ssh',
        name=ugettext_noop('Machine'),
        managed_by_tower=True,
        inputs={
            'fields': [{
                'id': 'username',
                'label': ugettext_noop('Username'),
                'type': 'string'
            }, {
                'id': 'password',
                'label': ugettext_noop('Password'),
                'type': 'string',
                'secret': True,
                'ask_at_runtime': True
            }, {
                'id': 'ssh_key_data',
                'label': ugettext_noop('SSH Private Key'),
                'type': 'string',
                'format': 'ssh_private_key',
                'secret': True,
                'multiline': True
            }, {
                'id': 'ssh_key_unlock',
                'label': ugettext_noop('Private Key Passphrase'),
                'type': 'string',
                'secret': True,
                'ask_at_runtime': True
            }, {
                'id': 'become_method',
                'label': ugettext_noop('Privilege Escalation Method'),
                'type': 'string',
                'help_text': ugettext_noop('Specify a method for "become" operations. This is '
                                           'equivalent to specifying the --become-method '
                                           'Ansible parameter.')
            }, {
                'id': 'become_username',
                'label': ugettext_noop('Privilege Escalation Username'),
                'type': 'string',
            }, {
                'id': 'become_password',
                'label': ugettext_noop('Privilege Escalation Password'),
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
        name=ugettext_noop('Source Control'),
        managed_by_tower=True,
        inputs={
            'fields': [{
                'id': 'username',
                'label': ugettext_noop('Username'),
                'type': 'string'
            }, {
                'id': 'password',
                'label': ugettext_noop('Password'),
                'type': 'string',
                'secret': True
            }, {
                'id': 'ssh_key_data',
                'label': ugettext_noop('SCM Private Key'),
                'type': 'string',
                'format': 'ssh_private_key',
                'secret': True,
                'multiline': True
            }, {
                'id': 'ssh_key_unlock',
                'label': ugettext_noop('Private Key Passphrase'),
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
        name=ugettext_noop('Vault'),
        managed_by_tower=True,
        inputs={
            'fields': [{
                'id': 'vault_password',
                'label': ugettext_noop('Vault Password'),
                'type': 'string',
                'secret': True,
                'ask_at_runtime': True
            }, {
                'id': 'vault_id',
                'label': ugettext_noop('Vault Identifier'),
                'type': 'string',
                'format': 'vault_id',
                'help_text': ugettext_noop('Specify an (optional) Vault ID. This is '
                                           'equivalent to specifying the --vault-id '
                                           'Ansible parameter for providing multiple Vault '
                                           'passwords.  Note: this feature only works in '
                                           'Ansible 2.4+.')
            }],
            'required': ['vault_password'],
        }
    )


@CredentialType.default
def net(cls):
    return cls(
        kind='net',
        name=ugettext_noop('Network'),
        managed_by_tower=True,
        inputs={
            'fields': [{
                'id': 'username',
                'label': ugettext_noop('Username'),
                'type': 'string'
            }, {
                'id': 'password',
                'label': ugettext_noop('Password'),
                'type': 'string',
                'secret': True,
            }, {
                'id': 'ssh_key_data',
                'label': ugettext_noop('SSH Private Key'),
                'type': 'string',
                'format': 'ssh_private_key',
                'secret': True,
                'multiline': True
            }, {
                'id': 'ssh_key_unlock',
                'label': ugettext_noop('Private Key Passphrase'),
                'type': 'string',
                'secret': True,
            }, {
                'id': 'authorize',
                'label': ugettext_noop('Authorize'),
                'type': 'boolean',
            }, {
                'id': 'authorize_password',
                'label': ugettext_noop('Authorize Password'),
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
        name=ugettext_noop('Amazon Web Services'),
        managed_by_tower=True,
        inputs={
            'fields': [{
                'id': 'username',
                'label': ugettext_noop('Access Key'),
                'type': 'string'
            }, {
                'id': 'password',
                'label': ugettext_noop('Secret Key'),
                'type': 'string',
                'secret': True,
            }, {
                'id': 'security_token',
                'label': ugettext_noop('STS Token'),
                'type': 'string',
                'secret': True,
                'help_text': ugettext_noop('Security Token Service (STS) is a web service '
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
        name=ugettext_noop('OpenStack'),
        managed_by_tower=True,
        inputs={
            'fields': [{
                'id': 'username',
                'label': ugettext_noop('Username'),
                'type': 'string'
            }, {
                'id': 'password',
                'label': ugettext_noop('Password (API Key)'),
                'type': 'string',
                'secret': True,
            }, {
                'id': 'host',
                'label': ugettext_noop('Host (Authentication URL)'),
                'type': 'string',
                'help_text': ugettext_noop('The host to authenticate with.  For example, '
                                           'https://openstack.business.com/v2.0/')
            }, {
                'id': 'project',
                'label': ugettext_noop('Project (Tenant Name)'),
                'type': 'string',
            }, {
                'id': 'domain',
                'label': ugettext_noop('Domain Name'),
                'type': 'string',
                'help_text': ugettext_noop('OpenStack domains define administrative boundaries. '
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
        name=ugettext_noop('VMware vCenter'),
        managed_by_tower=True,
        inputs={
            'fields': [{
                'id': 'host',
                'label': ugettext_noop('VCenter Host'),
                'type': 'string',
                'help_text': ugettext_noop('Enter the hostname or IP address that corresponds '
                                           'to your VMware vCenter.')
            }, {
                'id': 'username',
                'label': ugettext_noop('Username'),
                'type': 'string'
            }, {
                'id': 'password',
                'label': ugettext_noop('Password'),
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
        name=ugettext_noop('Red Hat Satellite 6'),
        managed_by_tower=True,
        inputs={
            'fields': [{
                'id': 'host',
                'label': ugettext_noop('Satellite 6 URL'),
                'type': 'string',
                'help_text': ugettext_noop('Enter the URL that corresponds to your Red Hat '
                                           'Satellite 6 server. For example, https://satellite.example.org')
            }, {
                'id': 'username',
                'label': ugettext_noop('Username'),
                'type': 'string'
            }, {
                'id': 'password',
                'label': ugettext_noop('Password'),
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
        name=ugettext_noop('Red Hat CloudForms'),
        managed_by_tower=True,
        inputs={
            'fields': [{
                'id': 'host',
                'label': ugettext_noop('CloudForms URL'),
                'type': 'string',
                'help_text': ugettext_noop('Enter the URL for the virtual machine that '
                                           'corresponds to your CloudForms instance. '
                                           'For example, https://cloudforms.example.org')
            }, {
                'id': 'username',
                'label': ugettext_noop('Username'),
                'type': 'string'
            }, {
                'id': 'password',
                'label': ugettext_noop('Password'),
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
        name=ugettext_noop('Google Compute Engine'),
        managed_by_tower=True,
        inputs={
            'fields': [{
                'id': 'username',
                'label': ugettext_noop('Service Account Email Address'),
                'type': 'string',
                'help_text': ugettext_noop('The email address assigned to the Google Compute '
                                           'Engine service account.')
            }, {
                'id': 'project',
                'label': 'Project',
                'type': 'string',
                'help_text': ugettext_noop('The Project ID is the GCE assigned identification. '
                                           'It is often constructed as three words or two words '
                                           'followed by a three-digit number. Examples: project-id-000 '
                                           'and another-project-id')
            }, {
                'id': 'ssh_key_data',
                'label': ugettext_noop('RSA Private Key'),
                'type': 'string',
                'format': 'ssh_private_key',
                'secret': True,
                'multiline': True,
                'help_text': ugettext_noop('Paste the contents of the PEM file associated '
                                           'with the service account email.')
            }],
            'required': ['username', 'ssh_key_data'],
        }
    )


@CredentialType.default
def azure_rm(cls):
    return cls(
        kind='cloud',
        name=ugettext_noop('Microsoft Azure Resource Manager'),
        managed_by_tower=True,
        inputs={
            'fields': [{
                'id': 'subscription',
                'label': ugettext_noop('Subscription ID'),
                'type': 'string',
                'help_text': ugettext_noop('Subscription ID is an Azure construct, which is '
                                           'mapped to a username.')
            }, {
                'id': 'username',
                'label': ugettext_noop('Username'),
                'type': 'string'
            }, {
                'id': 'password',
                'label': ugettext_noop('Password'),
                'type': 'string',
                'secret': True,
            }, {
                'id': 'client',
                'label': ugettext_noop('Client ID'),
                'type': 'string'
            }, {
                'id': 'secret',
                'label': ugettext_noop('Client Secret'),
                'type': 'string',
                'secret': True,
            }, {
                'id': 'tenant',
                'label': ugettext_noop('Tenant ID'),
                'type': 'string'
            }, {
                'id': 'cloud_environment',
                'label': ugettext_noop('Azure Cloud Environment'),
                'type': 'string',
                'help_text': ugettext_noop('Environment variable AZURE_CLOUD_ENVIRONMENT when'
                                           ' using Azure GovCloud or Azure stack.')
            }],
            'required': ['subscription'],
        }
    )


@CredentialType.default
def insights(cls):
    return cls(
        kind='insights',
        name=ugettext_noop('Insights'),
        managed_by_tower=True,
        inputs={
            'fields': [{
                'id': 'username',
                'label': ugettext_noop('Username'),
                'type': 'string'
            }, {
                'id': 'password',
                'label': ugettext_noop('Password'),
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


@CredentialType.default
def rhv(cls):
    return cls(
        kind='cloud',
        name=ugettext_noop('Red Hat Virtualization'),
        managed_by_tower=True,
        inputs={
            'fields': [{
                'id': 'host',
                'label': ugettext_noop('Host (Authentication URL)'),
                'type': 'string',
                'help_text': ugettext_noop('The host to authenticate with.')
            }, {
                'id': 'username',
                'label': ugettext_noop('Username'),
                'type': 'string'
            }, {
                'id': 'password',
                'label': ugettext_noop('Password'),
                'type': 'string',
                'secret': True,
            }, {
                'id': 'ca_file',
                'label': ugettext_noop('CA File'),
                'type': 'string',
                'help_text': ugettext_noop('Absolute file path to the CA file to use (optional)')
            }],
            'required': ['host', 'username', 'password'],
        },
        injectors={
            # The duplication here is intentional; the ovirt4 inventory plugin
            # writes a .ini file for authentication, while the ansible modules for
            # ovirt4 use a separate authentication process that support
            # environment variables; by injecting both, we support both
            'file': {
                'template': '\n'.join([
                    '[ovirt]',
                    'ovirt_url={{host}}',
                    'ovirt_username={{username}}',
                    'ovirt_password={{password}}',
                    '{% if ca_file %}ovirt_ca_file={{ca_file}}{% endif %}'])
            },
            'env': {
                'OVIRT_INI_PATH': '{{tower.filename}}',
                'OVIRT_URL': '{{host}}',
                'OVIRT_USERNAME': '{{username}}',
                'OVIRT_PASSWORD': '{{password}}'
            }
        },
    )


@CredentialType.default
def tower(cls):
    return cls(
        kind='cloud',
        name=ugettext_noop('Ansible Tower'),
        managed_by_tower=True,
        inputs={
            'fields': [{
                'id': 'host',
                'label': ugettext_noop('Ansible Tower Hostname'),
                'type': 'string',
                'help_text': ugettext_noop('The Ansible Tower base URL to authenticate with.')
            }, {
                'id': 'username',
                'label': ugettext_noop('Username'),
                'type': 'string'
            }, {
                'id': 'password',
                'label': ugettext_noop('Password'),
                'type': 'string',
                'secret': True,
            }, {
                'id': 'verify_ssl',
                'label': ugettext_noop('Verify SSL'),
                'type': 'boolean',
                'secret': False
            }],
            'required': ['host', 'username', 'password'],
        },
        injectors={
            'env': {
                'TOWER_HOST': '{{host}}',
                'TOWER_USERNAME': '{{username}}',
                'TOWER_PASSWORD': '{{password}}',
                'TOWER_VERIFY_SSL': '{{verify_ssl}}'
            }
        },
    )

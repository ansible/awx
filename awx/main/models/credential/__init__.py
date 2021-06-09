# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.
import functools
import inspect
import logging
import os
from pkg_resources import iter_entry_points
import re
import stat
import tempfile
from types import SimpleNamespace

# Jinja2
from jinja2 import sandbox

# Django
from django.db import models
from django.utils.translation import ugettext_lazy as _, ugettext_noop
from django.core.exceptions import ValidationError
from django.utils.encoding import force_text
from django.utils.functional import cached_property

# AWX
from awx.api.versioning import reverse
from awx.main.fields import (
    ImplicitRoleField,
    CredentialInputField,
    CredentialTypeInputField,
    CredentialTypeInjectorField,
    DynamicCredentialInputField,
)
from awx.main.utils import decrypt_field, classproperty
from awx.main.utils.safe_yaml import safe_dump
from awx.main.utils.execution_environments import to_container_path
from awx.main.validators import validate_ssh_private_key
from awx.main.models.base import CommonModelNameNotUnique, PasswordFieldsModel, PrimordialModel
from awx.main.models.mixins import ResourceMixin
from awx.main.models.rbac import (
    ROLE_SINGLETON_SYSTEM_ADMINISTRATOR,
    ROLE_SINGLETON_SYSTEM_AUDITOR,
)
from awx.main.utils import encrypt_field
from . import injectors as builtin_injectors

__all__ = ['Credential', 'CredentialType', 'CredentialInputSource', 'build_safe_env']

logger = logging.getLogger('awx.main.models.credential')
credential_plugins = dict((ep.name, ep.load()) for ep in iter_entry_points('awx.credential_plugins'))

HIDDEN_PASSWORD = '**********'


def build_safe_env(env):
    """
    Build environment dictionary, hiding potentially sensitive information
    such as passwords or keys.
    """
    hidden_re = re.compile(r'API|TOKEN|KEY|SECRET|PASS', re.I)
    urlpass_re = re.compile(r'^.*?://[^:]+:(.*?)@.*?$')
    safe_env = dict(env)
    for k, v in safe_env.items():
        if k == 'AWS_ACCESS_KEY_ID':
            continue
        elif k.startswith('ANSIBLE_') and not k.startswith('ANSIBLE_NET') and not k.startswith('ANSIBLE_GALAXY_SERVER'):
            continue
        elif hidden_re.search(k):
            safe_env[k] = HIDDEN_PASSWORD
        elif type(v) == str and urlpass_re.match(v):
            safe_env[k] = urlpass_re.sub(HIDDEN_PASSWORD, v)
    return safe_env


class Credential(PasswordFieldsModel, CommonModelNameNotUnique, ResourceMixin):
    """
    A credential contains information about how to talk to a remote resource
    Usually this is a SSH key location, and possibly an unlock password.
    If used with sudo, a sudo password should be set if required.
    """

    class Meta:
        app_label = 'main'
        ordering = ('name',)
        unique_together = ('organization', 'name', 'credential_type')

    PASSWORD_FIELDS = ['inputs']
    FIELDS_TO_PRESERVE_AT_COPY = ['input_sources']

    credential_type = models.ForeignKey(
        'CredentialType',
        related_name='credentials',
        null=False,
        on_delete=models.CASCADE,
        help_text=_('Specify the type of credential you want to create. Refer ' 'to the documentation for details on each type.'),
    )
    managed_by_tower = models.BooleanField(default=False, editable=False)
    organization = models.ForeignKey(
        'Organization',
        null=True,
        default=None,
        blank=True,
        on_delete=models.CASCADE,
        related_name='credentials',
    )
    inputs = CredentialInputField(
        blank=True, default=dict, help_text=_('Enter inputs using either JSON or YAML syntax. ' 'Refer to the documentation for example syntax.')
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
    read_role = ImplicitRoleField(
        parent_role=[
            'singleton:' + ROLE_SINGLETON_SYSTEM_AUDITOR,
            'organization.auditor_role',
            'use_role',
            'admin_role',
        ]
    )

    @property
    def kind(self):
        return self.credential_type.namespace

    @property
    def cloud(self):
        return self.credential_type.kind == 'cloud'

    @property
    def kubernetes(self):
        return self.credential_type.kind == 'kubernetes'

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
        return self.credential_type.kind == 'ssh' and self.inputs.get('password') == 'ASK'

    @property
    def has_encrypted_ssh_key_data(self):
        try:
            ssh_key_data = self.get_input('ssh_key_data')
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
        if self.credential_type.kind == 'ssh' and self.inputs.get('ssh_key_unlock') in ('ASK', ''):
            return self.has_encrypted_ssh_key_data
        return False

    @property
    def needs_become_password(self):
        return self.credential_type.kind == 'ssh' and self.inputs.get('become_password') == 'ASK'

    @property
    def needs_vault_password(self):
        return self.credential_type.kind == 'vault' and self.inputs.get('vault_password') == 'ASK'

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

    @cached_property
    def dynamic_input_fields(self):
        return [obj.input_field_name for obj in self.input_sources.all()]

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

    def mark_field_for_save(self, update_fields, field):
        if 'inputs' not in update_fields:
            update_fields.append('inputs')

    def encrypt_field(self, field, ask):
        if field not in self.inputs:
            return None
        encrypted = encrypt_field(self, field, ask=ask)
        if encrypted:
            self.inputs[field] = encrypted
        elif field in self.inputs:
            del self.inputs[field]

    def display_inputs(self):
        field_val = self.inputs.copy()
        for k, v in field_val.items():
            if force_text(v).startswith('$encrypted$'):
                field_val[k] = '$encrypted$'
        return field_val

    def unique_hash(self, display=False):
        """
        Credential exclusivity is not defined solely by the related
        credential type (due to vault), so this produces a hash
        that can be used to evaluate exclusivity
        """
        if display:
            type_alias = self.credential_type.name
        else:
            type_alias = self.credential_type_id
        if self.credential_type.kind == 'vault' and self.has_input('vault_id'):
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
        if self.credential_type.kind != 'external' and field_name in self.dynamic_input_fields:
            return self._get_dynamic_input(field_name)
        if field_name in self.credential_type.secret_fields:
            try:
                return decrypt_field(self, field_name)
            except AttributeError:
                for field in self.credential_type.inputs.get('fields', []):
                    if field['id'] == field_name and 'default' in field:
                        return field['default']
                if 'default' in kwargs:
                    return kwargs['default']
                raise AttributeError
        if field_name in self.inputs:
            return self.inputs[field_name]
        if 'default' in kwargs:
            return kwargs['default']
        for field in self.credential_type.inputs.get('fields', []):
            if field['id'] == field_name and 'default' in field:
                return field['default']
        raise AttributeError(field_name)

    def has_input(self, field_name):
        if field_name in self.dynamic_input_fields:
            return True
        return field_name in self.inputs and self.inputs[field_name] not in ('', None)

    def has_inputs(self, field_names=()):
        for name in field_names:
            if name in self.inputs:
                if self.inputs[name] in ('', None):
                    return False
            else:
                raise ValueError('{} is not an input field'.format(name))
        return True

    def _get_dynamic_input(self, field_name):
        for input_source in self.input_sources.all():
            if input_source.input_field_name == field_name:
                return input_source.get_input_value()
        else:
            raise ValueError('{} is not a dynamic input field'.format(field_name))


class CredentialType(CommonModelNameNotUnique):
    """
    A reusable schema for a credential.

    Used to define a named credential type with fields (e.g., an API key) and
    output injectors (i.e., an environment variable that uses the API key).
    """

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
        ('registry', _('Container Registry')),
        ('token', _('Personal Access Token')),
        ('insights', _('Insights')),
        ('external', _('External')),
        ('kubernetes', _('Kubernetes')),
        ('galaxy', _('Galaxy/Automation Hub')),
    )

    kind = models.CharField(max_length=32, choices=KIND_CHOICES)
    managed_by_tower = models.BooleanField(default=False, editable=False)
    namespace = models.CharField(max_length=1024, null=True, default=None, editable=False)
    inputs = CredentialTypeInputField(
        blank=True, default=dict, help_text=_('Enter inputs using either JSON or YAML syntax. ' 'Refer to the documentation for example syntax.')
    )
    injectors = CredentialTypeInjectorField(
        blank=True,
        default=dict,
        help_text=_('Enter injectors using either JSON or YAML syntax. ' 'Refer to the documentation for example syntax.'),
    )

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super(CredentialType, cls).from_db(db, field_names, values)
        if instance.managed_by_tower and instance.namespace:
            native = ManagedCredentialType.registry[instance.namespace]
            instance.inputs = native.inputs
            instance.injectors = native.injectors
        return instance

    def get_absolute_url(self, request=None):
        return reverse('api:credential_type_detail', kwargs={'pk': self.pk}, request=request)

    @property
    def defined_fields(self):
        return [field.get('id') for field in self.inputs.get('fields', [])]

    @property
    def secret_fields(self):
        return [field['id'] for field in self.inputs.get('fields', []) if field.get('secret', False) is True]

    @property
    def askable_fields(self):
        return [field['id'] for field in self.inputs.get('fields', []) if field.get('ask_at_runtime', False) is True]

    @property
    def plugin(self):
        if self.kind != 'external':
            raise AttributeError('plugin')
        [plugin] = [plugin for ns, plugin in credential_plugins.items() if ns == self.namespace]
        return plugin

    def default_for_field(self, field_id):
        for field in self.inputs.get('fields', []):
            if field['id'] == field_id:
                if 'choices' in field:
                    return field['choices'][0]
                return {'string': '', 'boolean': False}[field['type']]

    @classproperty
    def defaults(cls):
        return dict((k, functools.partial(v.create)) for k, v in ManagedCredentialType.registry.items())

    @classmethod
    def setup_tower_managed_defaults(cls):
        for default in ManagedCredentialType.registry.values():
            existing = CredentialType.objects.filter(name=default.name, kind=default.kind).first()
            if existing is not None:
                existing.namespace = default.namespace
                existing.inputs = {}
                existing.injectors = {}
                existing.save()
                continue
            logger.debug(_("adding %s credential type" % default.name))
            created = default.create()
            created.inputs = created.injectors = {}
            created.save()

    @classmethod
    def load_plugin(cls, ns, plugin):
        ManagedCredentialType(namespace=ns, name=plugin.name, kind='external', inputs=plugin.inputs)

    def inject_credential(self, credential, env, safe_env, args, private_data_dir):
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
        :param private_data_dir: a temporary directory to store files generated
                                 by `file` injectors (like config files or key
                                 files)
        """
        if not self.injectors:
            if self.managed_by_tower and credential.credential_type.namespace in dir(builtin_injectors):
                injected_env = {}
                getattr(builtin_injectors, credential.credential_type.namespace)(credential, injected_env, private_data_dir)
                env.update(injected_env)
                safe_env.update(build_safe_env(injected_env))
            return

        class TowerNamespace:
            pass

        tower_namespace = TowerNamespace()

        # maintain a normal namespace for building the ansible-playbook arguments (env and args)
        namespace = {'tower': tower_namespace}

        # maintain a sanitized namespace for building the DB-stored arguments (safe_env)
        safe_namespace = {'tower': tower_namespace}

        # build a normal namespace with secret values decrypted (for
        # ansible-playbook) and a safe namespace with secret values hidden (for
        # DB storage)
        injectable_fields = list(credential.inputs.keys()) + credential.dynamic_input_fields
        for field_name in list(set(injectable_fields)):
            value = credential.get_input(field_name)

            if type(value) is bool:
                # boolean values can't be secret/encrypted/external
                safe_namespace[field_name] = namespace[field_name] = value
                continue

            if field_name in self.secret_fields:
                safe_namespace[field_name] = '**********'
            elif len(value):
                safe_namespace[field_name] = value
            if len(value):
                namespace[field_name] = value

        for field in self.inputs.get('fields', []):
            # default missing boolean fields to False
            if field['type'] == 'boolean' and field['id'] not in credential.inputs.keys():
                namespace[field['id']] = safe_namespace[field['id']] = False
            # make sure private keys end with a \n
            if field.get('format') == 'ssh_private_key':
                if field['id'] in namespace and not namespace[field['id']].endswith('\n'):
                    namespace[field['id']] += '\n'

        file_tmpls = self.injectors.get('file', {})
        # If any file templates are provided, render the files and update the
        # special `tower` template namespace so the filename can be
        # referenced in other injectors

        sandbox_env = sandbox.ImmutableSandboxedEnvironment()

        for file_label, file_tmpl in file_tmpls.items():
            data = sandbox_env.from_string(file_tmpl).render(**namespace)
            _, path = tempfile.mkstemp(dir=os.path.join(private_data_dir, 'env'))
            with open(path, 'w') as f:
                f.write(data)
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
            container_path = to_container_path(path, private_data_dir)

            # determine if filename indicates single file or many
            if file_label.find('.') == -1:
                tower_namespace.filename = container_path
            else:
                if not hasattr(tower_namespace, 'filename'):
                    tower_namespace.filename = TowerNamespace()
                file_label = file_label.split('.')[1]
                setattr(tower_namespace.filename, file_label, container_path)

        injector_field = self._meta.get_field('injectors')
        for env_var, tmpl in self.injectors.get('env', {}).items():
            try:
                injector_field.validate_env_var_allowed(env_var)
            except ValidationError as e:
                logger.error('Ignoring prohibited env var {}, reason: {}'.format(env_var, e))
                continue
            env[env_var] = sandbox_env.from_string(tmpl).render(**namespace)
            safe_env[env_var] = sandbox_env.from_string(tmpl).render(**safe_namespace)

        if 'INVENTORY_UPDATE_ID' not in env:
            # awx-manage inventory_update does not support extra_vars via -e
            extra_vars = {}
            for var_name, tmpl in self.injectors.get('extra_vars', {}).items():
                extra_vars[var_name] = sandbox_env.from_string(tmpl).render(**namespace)

            def build_extra_vars_file(vars, private_dir):
                handle, path = tempfile.mkstemp(dir=os.path.join(private_dir, 'env'))
                f = os.fdopen(handle, 'w')
                f.write(safe_dump(vars))
                f.close()
                os.chmod(path, stat.S_IRUSR)
                return path

            if extra_vars:
                path = build_extra_vars_file(extra_vars, private_data_dir)
                container_path = to_container_path(path, private_data_dir)
                args.extend(['-e', '@%s' % container_path])


class ManagedCredentialType(SimpleNamespace):

    registry = {}

    def __init__(self, namespace, **kwargs):
        for k in ('inputs', 'injectors'):
            if k not in kwargs:
                kwargs[k] = {}
        super(ManagedCredentialType, self).__init__(namespace=namespace, **kwargs)
        if namespace in ManagedCredentialType.registry:
            raise ValueError(
                'a ManagedCredentialType with namespace={} is already defined in {}'.format(
                    namespace, inspect.getsourcefile(ManagedCredentialType.registry[namespace].__class__)
                )
            )
        ManagedCredentialType.registry[namespace] = self

    def create(self):
        return CredentialType(
            namespace=self.namespace,
            kind=self.kind,
            name=self.name,
            managed_by_tower=True,
            inputs=self.inputs,
            injectors=self.injectors,
        )


ManagedCredentialType(
    namespace='ssh',
    kind='ssh',
    name=ugettext_noop('Machine'),
    inputs={
        'fields': [
            {'id': 'username', 'label': ugettext_noop('Username'), 'type': 'string'},
            {'id': 'password', 'label': ugettext_noop('Password'), 'type': 'string', 'secret': True, 'ask_at_runtime': True},
            {'id': 'ssh_key_data', 'label': ugettext_noop('SSH Private Key'), 'type': 'string', 'format': 'ssh_private_key', 'secret': True, 'multiline': True},
            {
                'id': 'ssh_public_key_data',
                'label': ugettext_noop('Signed SSH Certificate'),
                'type': 'string',
                'multiline': True,
                'secret': True,
            },
            {'id': 'ssh_key_unlock', 'label': ugettext_noop('Private Key Passphrase'), 'type': 'string', 'secret': True, 'ask_at_runtime': True},
            {
                'id': 'become_method',
                'label': ugettext_noop('Privilege Escalation Method'),
                'type': 'string',
                'help_text': ugettext_noop(
                    'Specify a method for "become" operations. This is ' 'equivalent to specifying the --become-method ' 'Ansible parameter.'
                ),
            },
            {
                'id': 'become_username',
                'label': ugettext_noop('Privilege Escalation Username'),
                'type': 'string',
            },
            {'id': 'become_password', 'label': ugettext_noop('Privilege Escalation Password'), 'type': 'string', 'secret': True, 'ask_at_runtime': True},
        ],
    },
)

ManagedCredentialType(
    namespace='scm',
    kind='scm',
    name=ugettext_noop('Source Control'),
    managed_by_tower=True,
    inputs={
        'fields': [
            {'id': 'username', 'label': ugettext_noop('Username'), 'type': 'string'},
            {'id': 'password', 'label': ugettext_noop('Password'), 'type': 'string', 'secret': True},
            {'id': 'ssh_key_data', 'label': ugettext_noop('SCM Private Key'), 'type': 'string', 'format': 'ssh_private_key', 'secret': True, 'multiline': True},
            {'id': 'ssh_key_unlock', 'label': ugettext_noop('Private Key Passphrase'), 'type': 'string', 'secret': True},
        ],
    },
)

ManagedCredentialType(
    namespace='vault',
    kind='vault',
    name=ugettext_noop('Vault'),
    managed_by_tower=True,
    inputs={
        'fields': [
            {'id': 'vault_password', 'label': ugettext_noop('Vault Password'), 'type': 'string', 'secret': True, 'ask_at_runtime': True},
            {
                'id': 'vault_id',
                'label': ugettext_noop('Vault Identifier'),
                'type': 'string',
                'format': 'vault_id',
                'help_text': ugettext_noop(
                    'Specify an (optional) Vault ID. This is '
                    'equivalent to specifying the --vault-id '
                    'Ansible parameter for providing multiple Vault '
                    'passwords.  Note: this feature only works in '
                    'Ansible 2.4+.'
                ),
            },
        ],
        'required': ['vault_password'],
    },
)

ManagedCredentialType(
    namespace='net',
    kind='net',
    name=ugettext_noop('Network'),
    managed_by_tower=True,
    inputs={
        'fields': [
            {'id': 'username', 'label': ugettext_noop('Username'), 'type': 'string'},
            {
                'id': 'password',
                'label': ugettext_noop('Password'),
                'type': 'string',
                'secret': True,
            },
            {'id': 'ssh_key_data', 'label': ugettext_noop('SSH Private Key'), 'type': 'string', 'format': 'ssh_private_key', 'secret': True, 'multiline': True},
            {
                'id': 'ssh_key_unlock',
                'label': ugettext_noop('Private Key Passphrase'),
                'type': 'string',
                'secret': True,
            },
            {
                'id': 'authorize',
                'label': ugettext_noop('Authorize'),
                'type': 'boolean',
            },
            {
                'id': 'authorize_password',
                'label': ugettext_noop('Authorize Password'),
                'type': 'string',
                'secret': True,
            },
        ],
        'dependencies': {
            'authorize_password': ['authorize'],
        },
        'required': ['username'],
    },
)

ManagedCredentialType(
    namespace='aws',
    kind='cloud',
    name=ugettext_noop('Amazon Web Services'),
    managed_by_tower=True,
    inputs={
        'fields': [
            {'id': 'username', 'label': ugettext_noop('Access Key'), 'type': 'string'},
            {
                'id': 'password',
                'label': ugettext_noop('Secret Key'),
                'type': 'string',
                'secret': True,
            },
            {
                'id': 'security_token',
                'label': ugettext_noop('STS Token'),
                'type': 'string',
                'secret': True,
                'help_text': ugettext_noop(
                    'Security Token Service (STS) is a web service '
                    'that enables you to request temporary, '
                    'limited-privilege credentials for AWS Identity '
                    'and Access Management (IAM) users.'
                ),
            },
        ],
        'required': ['username', 'password'],
    },
)

ManagedCredentialType(
    namespace='openstack',
    kind='cloud',
    name=ugettext_noop('OpenStack'),
    managed_by_tower=True,
    inputs={
        'fields': [
            {'id': 'username', 'label': ugettext_noop('Username'), 'type': 'string'},
            {
                'id': 'password',
                'label': ugettext_noop('Password (API Key)'),
                'type': 'string',
                'secret': True,
            },
            {
                'id': 'host',
                'label': ugettext_noop('Host (Authentication URL)'),
                'type': 'string',
                'help_text': ugettext_noop('The host to authenticate with.  For example, ' 'https://openstack.business.com/v2.0/'),
            },
            {
                'id': 'project',
                'label': ugettext_noop('Project (Tenant Name)'),
                'type': 'string',
            },
            {
                'id': 'project_domain_name',
                'label': ugettext_noop('Project (Domain Name)'),
                'type': 'string',
            },
            {
                'id': 'domain',
                'label': ugettext_noop('Domain Name'),
                'type': 'string',
                'help_text': ugettext_noop(
                    'OpenStack domains define administrative boundaries. '
                    'It is only needed for Keystone v3 authentication '
                    'URLs. Refer to the documentation for '
                    'common scenarios.'
                ),
            },
            {
                'id': 'region',
                'label': ugettext_noop('Region Name'),
                'type': 'string',
                'help_text': ugettext_noop('For some cloud providers, like OVH, region must be specified'),
            },
            {
                'id': 'verify_ssl',
                'label': ugettext_noop('Verify SSL'),
                'type': 'boolean',
                'default': True,
            },
        ],
        'required': ['username', 'password', 'host', 'project'],
    },
)

ManagedCredentialType(
    namespace='vmware',
    kind='cloud',
    name=ugettext_noop('VMware vCenter'),
    managed_by_tower=True,
    inputs={
        'fields': [
            {
                'id': 'host',
                'label': ugettext_noop('VCenter Host'),
                'type': 'string',
                'help_text': ugettext_noop('Enter the hostname or IP address that corresponds ' 'to your VMware vCenter.'),
            },
            {'id': 'username', 'label': ugettext_noop('Username'), 'type': 'string'},
            {
                'id': 'password',
                'label': ugettext_noop('Password'),
                'type': 'string',
                'secret': True,
            },
        ],
        'required': ['host', 'username', 'password'],
    },
)

ManagedCredentialType(
    namespace='satellite6',
    kind='cloud',
    name=ugettext_noop('Red Hat Satellite 6'),
    managed_by_tower=True,
    inputs={
        'fields': [
            {
                'id': 'host',
                'label': ugettext_noop('Satellite 6 URL'),
                'type': 'string',
                'help_text': ugettext_noop('Enter the URL that corresponds to your Red Hat ' 'Satellite 6 server. For example, https://satellite.example.org'),
            },
            {'id': 'username', 'label': ugettext_noop('Username'), 'type': 'string'},
            {
                'id': 'password',
                'label': ugettext_noop('Password'),
                'type': 'string',
                'secret': True,
            },
        ],
        'required': ['host', 'username', 'password'],
    },
)

ManagedCredentialType(
    namespace='gce',
    kind='cloud',
    name=ugettext_noop('Google Compute Engine'),
    managed_by_tower=True,
    inputs={
        'fields': [
            {
                'id': 'username',
                'label': ugettext_noop('Service Account Email Address'),
                'type': 'string',
                'help_text': ugettext_noop('The email address assigned to the Google Compute ' 'Engine service account.'),
            },
            {
                'id': 'project',
                'label': 'Project',
                'type': 'string',
                'help_text': ugettext_noop(
                    'The Project ID is the GCE assigned identification. '
                    'It is often constructed as three words or two words '
                    'followed by a three-digit number. Examples: project-id-000 '
                    'and another-project-id'
                ),
            },
            {
                'id': 'ssh_key_data',
                'label': ugettext_noop('RSA Private Key'),
                'type': 'string',
                'format': 'ssh_private_key',
                'secret': True,
                'multiline': True,
                'help_text': ugettext_noop('Paste the contents of the PEM file associated ' 'with the service account email.'),
            },
        ],
        'required': ['username', 'ssh_key_data'],
    },
)

ManagedCredentialType(
    namespace='azure_rm',
    kind='cloud',
    name=ugettext_noop('Microsoft Azure Resource Manager'),
    managed_by_tower=True,
    inputs={
        'fields': [
            {
                'id': 'subscription',
                'label': ugettext_noop('Subscription ID'),
                'type': 'string',
                'help_text': ugettext_noop('Subscription ID is an Azure construct, which is ' 'mapped to a username.'),
            },
            {'id': 'username', 'label': ugettext_noop('Username'), 'type': 'string'},
            {
                'id': 'password',
                'label': ugettext_noop('Password'),
                'type': 'string',
                'secret': True,
            },
            {'id': 'client', 'label': ugettext_noop('Client ID'), 'type': 'string'},
            {
                'id': 'secret',
                'label': ugettext_noop('Client Secret'),
                'type': 'string',
                'secret': True,
            },
            {'id': 'tenant', 'label': ugettext_noop('Tenant ID'), 'type': 'string'},
            {
                'id': 'cloud_environment',
                'label': ugettext_noop('Azure Cloud Environment'),
                'type': 'string',
                'help_text': ugettext_noop('Environment variable AZURE_CLOUD_ENVIRONMENT when' ' using Azure GovCloud or Azure stack.'),
            },
        ],
        'required': ['subscription'],
    },
)

ManagedCredentialType(
    namespace='github_token',
    kind='token',
    name=ugettext_noop('GitHub Personal Access Token'),
    managed_by_tower=True,
    inputs={
        'fields': [
            {
                'id': 'token',
                'label': ugettext_noop('Token'),
                'type': 'string',
                'secret': True,
                'help_text': ugettext_noop('This token needs to come from your profile settings in GitHub'),
            }
        ],
        'required': ['token'],
    },
)

ManagedCredentialType(
    namespace='gitlab_token',
    kind='token',
    name=ugettext_noop('GitLab Personal Access Token'),
    managed_by_tower=True,
    inputs={
        'fields': [
            {
                'id': 'token',
                'label': ugettext_noop('Token'),
                'type': 'string',
                'secret': True,
                'help_text': ugettext_noop('This token needs to come from your profile settings in GitLab'),
            }
        ],
        'required': ['token'],
    },
)

ManagedCredentialType(
    namespace='insights',
    kind='insights',
    name=ugettext_noop('Insights'),
    managed_by_tower=True,
    inputs={
        'fields': [
            {'id': 'username', 'label': ugettext_noop('Username'), 'type': 'string'},
            {'id': 'password', 'label': ugettext_noop('Password'), 'type': 'string', 'secret': True},
        ],
        'required': ['username', 'password'],
    },
    injectors={
        'extra_vars': {
            "scm_username": "{{username}}",
            "scm_password": "{{password}}",
        },
        'env': {
            'INSIGHTS_USER': '{{username}}',
            'INSIGHTS_PASSWORD': '{{password}}',
        },
    },
)

ManagedCredentialType(
    namespace='rhv',
    kind='cloud',
    name=ugettext_noop('Red Hat Virtualization'),
    managed_by_tower=True,
    inputs={
        'fields': [
            {'id': 'host', 'label': ugettext_noop('Host (Authentication URL)'), 'type': 'string', 'help_text': ugettext_noop('The host to authenticate with.')},
            {'id': 'username', 'label': ugettext_noop('Username'), 'type': 'string'},
            {
                'id': 'password',
                'label': ugettext_noop('Password'),
                'type': 'string',
                'secret': True,
            },
            {
                'id': 'ca_file',
                'label': ugettext_noop('CA File'),
                'type': 'string',
                'help_text': ugettext_noop('Absolute file path to the CA file to use (optional)'),
            },
        ],
        'required': ['host', 'username', 'password'],
    },
    injectors={
        # The duplication here is intentional; the ovirt4 inventory plugin
        # writes a .ini file for authentication, while the ansible modules for
        # ovirt4 use a separate authentication process that support
        # environment variables; by injecting both, we support both
        'file': {
            'template': '\n'.join(
                [
                    '[ovirt]',
                    'ovirt_url={{host}}',
                    'ovirt_username={{username}}',
                    'ovirt_password={{password}}',
                    '{% if ca_file %}ovirt_ca_file={{ca_file}}{% endif %}',
                ]
            )
        },
        'env': {'OVIRT_INI_PATH': '{{tower.filename}}', 'OVIRT_URL': '{{host}}', 'OVIRT_USERNAME': '{{username}}', 'OVIRT_PASSWORD': '{{password}}'},
    },
)

ManagedCredentialType(
    namespace='tower',
    kind='cloud',
    name=ugettext_noop('Ansible Tower'),
    managed_by_tower=True,
    inputs={
        'fields': [
            {
                'id': 'host',
                'label': ugettext_noop('Ansible Tower Hostname'),
                'type': 'string',
                'help_text': ugettext_noop('The Ansible Tower base URL to authenticate with.'),
            },
            {
                'id': 'username',
                'label': ugettext_noop('Username'),
                'type': 'string',
                'help_text': ugettext_noop('The Ansible Tower user to authenticate as.' 'This should not be set if an OAuth token is being used.'),
            },
            {
                'id': 'password',
                'label': ugettext_noop('Password'),
                'type': 'string',
                'secret': True,
            },
            {
                'id': 'oauth_token',
                'label': ugettext_noop('OAuth Token'),
                'type': 'string',
                'secret': True,
                'help_text': ugettext_noop('An OAuth token to use to authenticate with.' 'This should not be set if username/password are being used.'),
            },
            {'id': 'verify_ssl', 'label': ugettext_noop('Verify SSL'), 'type': 'boolean', 'secret': False},
        ],
        'required': ['host'],
    },
    injectors={
        'env': {
            'TOWER_HOST': '{{host}}',
            'TOWER_USERNAME': '{{username}}',
            'TOWER_PASSWORD': '{{password}}',
            'TOWER_VERIFY_SSL': '{{verify_ssl}}',
            'TOWER_OAUTH_TOKEN': '{{oauth_token}}',
        }
    },
)

ManagedCredentialType(
    namespace='kubernetes_bearer_token',
    kind='kubernetes',
    name=ugettext_noop('OpenShift or Kubernetes API Bearer Token'),
    inputs={
        'fields': [
            {
                'id': 'host',
                'label': ugettext_noop('OpenShift or Kubernetes API Endpoint'),
                'type': 'string',
                'help_text': ugettext_noop('The OpenShift or Kubernetes API Endpoint to authenticate with.'),
            },
            {
                'id': 'bearer_token',
                'label': ugettext_noop('API authentication bearer token'),
                'type': 'string',
                'secret': True,
            },
            {
                'id': 'verify_ssl',
                'label': ugettext_noop('Verify SSL'),
                'type': 'boolean',
                'default': True,
            },
            {
                'id': 'ssl_ca_cert',
                'label': ugettext_noop('Certificate Authority data'),
                'type': 'string',
                'secret': True,
                'multiline': True,
            },
        ],
        'required': ['host', 'bearer_token'],
    },
)

ManagedCredentialType(
    namespace='registry',
    kind='registry',
    name=ugettext_noop('Container Registry'),
    inputs={
        'fields': [
            {
                'id': 'host',
                'label': ugettext_noop('Authentication URL'),
                'type': 'string',
                'help_text': ugettext_noop('Authentication endpoint for the container registry.'),
            },
            {
                'id': 'username',
                'label': ugettext_noop('Username'),
                'type': 'string',
            },
            {
                'id': 'password',
                'label': ugettext_noop('Password or Token'),
                'type': 'string',
                'secret': True,
                'help_text': ugettext_noop('A password or token used to authenticate with'),
            },
            {
                'id': 'verify_ssl',
                'label': ugettext_noop('Verify SSL'),
                'type': 'boolean',
                'default': True,
            },
        ],
        'required': ['host'],
    },
)


ManagedCredentialType(
    namespace='galaxy_api_token',
    kind='galaxy',
    name=ugettext_noop('Ansible Galaxy/Automation Hub API Token'),
    inputs={
        'fields': [
            {
                'id': 'url',
                'label': ugettext_noop('Galaxy Server URL'),
                'type': 'string',
                'help_text': ugettext_noop('The URL of the Galaxy instance to connect to.'),
            },
            {
                'id': 'auth_url',
                'label': ugettext_noop('Auth Server URL'),
                'type': 'string',
                'help_text': ugettext_noop('The URL of a Keycloak server token_endpoint, if using ' 'SSO auth.'),
            },
            {
                'id': 'token',
                'label': ugettext_noop('API Token'),
                'type': 'string',
                'secret': True,
                'help_text': ugettext_noop('A token to use for authentication against the Galaxy instance.'),
            },
        ],
        'required': ['url'],
    },
)


class CredentialInputSource(PrimordialModel):
    class Meta:
        app_label = 'main'
        unique_together = (('target_credential', 'input_field_name'),)
        ordering = (
            'target_credential',
            'source_credential',
            'input_field_name',
        )

    FIELDS_TO_PRESERVE_AT_COPY = ['source_credential', 'metadata', 'input_field_name']

    target_credential = models.ForeignKey(
        'Credential',
        related_name='input_sources',
        on_delete=models.CASCADE,
        null=True,
    )
    source_credential = models.ForeignKey(
        'Credential',
        related_name='target_input_sources',
        on_delete=models.CASCADE,
        null=True,
    )
    input_field_name = models.CharField(
        max_length=1024,
    )
    metadata = DynamicCredentialInputField(blank=True, default=dict)

    def clean_target_credential(self):
        if self.target_credential.credential_type.kind == 'external':
            raise ValidationError(_('Target must be a non-external credential'))
        return self.target_credential

    def clean_source_credential(self):
        if self.source_credential.credential_type.kind != 'external':
            raise ValidationError(_('Source must be an external credential'))
        return self.source_credential

    def clean_input_field_name(self):
        defined_fields = self.target_credential.credential_type.defined_fields
        if self.input_field_name not in defined_fields:
            raise ValidationError(_('Input field must be defined on target credential (options are {}).'.format(', '.join(sorted(defined_fields)))))
        return self.input_field_name

    def get_input_value(self):
        backend = self.source_credential.credential_type.plugin.backend
        backend_kwargs = {}
        for field_name, value in self.source_credential.inputs.items():
            if field_name in self.source_credential.credential_type.secret_fields:
                backend_kwargs[field_name] = decrypt_field(self.source_credential, field_name)
            else:
                backend_kwargs[field_name] = value

        backend_kwargs.update(self.metadata)
        return backend(**backend_kwargs)

    def get_absolute_url(self, request=None):
        view_name = 'api:credential_input_source_detail'
        return reverse(view_name, kwargs={'pk': self.pk}, request=request)


for ns, plugin in credential_plugins.items():
    CredentialType.load_plugin(ns, plugin)

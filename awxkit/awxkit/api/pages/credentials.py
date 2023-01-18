import logging

import http.client as http

import awxkit.exceptions as exc
from awxkit.api.mixins import DSAdapter, HasCopy, HasCreate
from awxkit.api.pages import Organization, Team, User
from awxkit.api.resources import resources
from awxkit.config import config
from awxkit.utils import (
    PseudoNamespace,
    cloud_types,
    filter_by_class,
    not_provided,
    random_title,
    update_payload,
)

from . import base, page
from .page import exception_from_status_code

from urllib.parse import urljoin


log = logging.getLogger(__name__)


credential_input_fields = (
    'authorize_password',
    'become_method',
    'become_password',
    'become_username',
    'client',
    'cloud_environment',
    'domain',
    'host',
    'password',
    'project_id',
    'project_name',
    'secret',
    'ssh_key_data',
    'ssh_key_unlock',
    'subscription',
    'tenant',
    'username',
    'vault_password',
    'vault_id',
    'gpg_public_key',
)


def generate_private_key():
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    key = rsa.generate_private_key(public_exponent=65537, key_size=4096, backend=default_backend())
    return key.private_bytes(
        encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.TraditionalOpenSSL, encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')


def config_cred_from_kind(kind):
    try:
        if kind == 'net':
            config_cred = config.credentials.network
        elif kind in cloud_types:
            if kind == 'azure_rm':
                config_cred = config.credentials.cloud.azure
            else:
                config_cred = config.credentials.cloud[kind]
        else:
            config_cred = config.credentials[kind]
        return config_cred
    except (KeyError, AttributeError):
        return PseudoNamespace()


credential_type_name_to_config_kind_map = {
    'amazon web services': 'aws',
    'container registry': 'registry',
    'ansible galaxy/automation hub api token': 'galaxy',
    'red hat ansible automation platform': 'controller',
    'google compute engine': 'gce',
    'insights': 'insights',
    'openshift or kubernetes api bearer token': 'kubernetes',
    'microsoft azure classic (deprecated)': 'azure_classic',
    'microsoft azure resource manager': 'azure_rm',
    'network': 'net',
    'openstack': 'OpenStack',
    'red hat virtualization': 'rhv',
    'red hat cloudforms': 'cloudforms',
    'red hat satellite 6': 'satellite6',
    'source control': 'scm',
    'machine': 'ssh',
    'vault': 'vault',
    'vmware vcenter': 'vmware',
    'gpg public key': 'gpg_public_key',
}

config_kind_to_credential_type_name_map = {kind: name for name, kind in credential_type_name_to_config_kind_map.items()}


def kind_and_config_cred_from_credential_type(credential_type):
    kind = ''

    if not credential_type.managed:
        return kind, PseudoNamespace()
    try:
        if credential_type.kind == 'net':
            config_cred = config.credentials.network
            kind = 'net'
        elif credential_type.kind == 'cloud':
            kind = credential_type_name_to_config_kind_map[credential_type.name.lower()]
            config_kind = kind if kind != 'azure_rm' else 'azure'
            config_cred = config.credentials.cloud[config_kind]
        else:
            kind = credential_type.kind.lower()
            config_cred = config.credentials[kind]
        return kind, config_cred
    except (KeyError, AttributeError):
        return kind, PseudoNamespace()


def get_payload_field_and_value_from_kwargs_or_config_cred(field, kind, kwargs, config_cred):
    if field in ('project_id', 'project_name'):  # Needed to prevent Project kwarg collision
        config_field = 'project'
    elif field == 'subscription' and 'azure' in kind:
        config_field = 'subscription_id'
    elif field == 'username' and kind == 'azure_ad':
        config_field = 'ad_user'
    elif field == 'client':
        config_field = 'client_id'
    elif field == 'authorize_password':
        config_field = 'authorize'
    else:
        config_field = field
    value = kwargs.get(field, config_cred.get(config_field, not_provided))
    if field in ('project_id', 'project_name'):
        field = 'project'
    return field, value


class CredentialType(HasCreate, base.Base):

    NATURAL_KEY = ('name', 'kind')

    def silent_delete(self):
        if not self.managed:
            return super(CredentialType, self).silent_delete()

    def payload(self, kind='cloud', **kwargs):
        payload = PseudoNamespace(
            name=kwargs.get('name') or 'CredentialType - {}'.format(random_title()), description=kwargs.get('description') or random_title(10), kind=kind
        )
        fields = ('inputs', 'injectors')
        update_payload(payload, fields, kwargs)
        return payload

    def create_payload(self, kind='cloud', **kwargs):
        payload = self.payload(kind=kind, **kwargs)
        payload.ds = DSAdapter(self.__class__.__name__, self._dependency_store)
        return payload

    def create(self, kind='cloud', **kwargs):
        payload = self.create_payload(kind=kind, **kwargs)
        return self.update_identity(CredentialTypes(self.connection).post(payload))

    def test(self, data):
        """Test the credential type endpoint."""
        response = self.connection.post(urljoin(str(self.url), 'test/'), data)
        exception = exception_from_status_code(response.status_code)
        exc_str = "%s (%s) received" % (http.responses[response.status_code], response.status_code)
        if exception:
            raise exception(exc_str, response.json())
        elif response.status_code == http.FORBIDDEN:
            raise exc.Forbidden(exc_str, response.json())
        return response


page.register_page([resources.credential_type, (resources.credential_types, 'post')], CredentialType)


class CredentialTypes(page.PageList, CredentialType):

    pass


page.register_page(resources.credential_types, CredentialTypes)


class Credential(HasCopy, HasCreate, base.Base):

    dependencies = [CredentialType]
    optional_dependencies = [Organization, User, Team]
    NATURAL_KEY = ('organization', 'name', 'credential_type')

    def payload(self, credential_type, user=None, team=None, organization=None, inputs=None, **kwargs):
        if not any((user, team, organization)):
            raise TypeError('{0.__class__.__name__} requires user, team, and/or organization instances.'.format(self))

        if inputs is None:
            inputs = {}

        payload = PseudoNamespace(
            name=kwargs.get('name') or 'Credential - {}'.format(random_title()),
            description=kwargs.get('description') or random_title(10),
            credential_type=credential_type.id,
            inputs=inputs,
        )
        if user:
            payload.user = user.id
        if team:
            payload.team = team.id
        if organization:
            payload.organization = organization.id

        kind, config_cred = kind_and_config_cred_from_credential_type(credential_type)

        for field in credential_input_fields:
            field, value = get_payload_field_and_value_from_kwargs_or_config_cred(field, kind, inputs or kwargs, config_cred)
            if value != not_provided:
                payload.inputs[field] = value

        if kind == 'net':
            payload.inputs.authorize = inputs.get('authorize', bool(inputs.get('authorize_password')))

        if kind in ('ssh', 'net') and 'ssh_key_data' not in payload.inputs:
            payload.inputs.ssh_key_data = inputs.get('ssh_key_data', generate_private_key())

        return payload

    def create_payload(self, credential_type=CredentialType, user=None, team=None, organization=Organization, inputs=None, **kwargs):
        if isinstance(credential_type, int):
            # if an int was passed, it is assumed to be the pk id of a
            # credential type
            credential_type = CredentialTypes(self.connection).get(id=credential_type).results.pop()

        if credential_type == CredentialType:
            kind = kwargs.pop('kind', 'ssh')
            if kind in ('openstack', 'openstack_v3'):
                credential_type_name = 'OpenStack'
                if inputs is None:
                    if kind == 'openstack_v3':
                        inputs = config.credentials.cloud['openstack_v3']
                    else:
                        inputs = config.credentials.cloud['openstack']
            else:
                credential_type_name = config_kind_to_credential_type_name_map[kind]
            credential_type = CredentialTypes(self.connection).get(managed=True, name__icontains=credential_type_name).results.pop()

        credential_type, organization, user, team = filter_by_class((credential_type, CredentialType), (organization, Organization), (user, User), (team, Team))
        if not any((user, team, organization)):
            organization = Organization
        self.create_and_update_dependencies(credential_type, organization, user, team)
        user = self.ds.user if user else None
        team = self.ds.team if team else None
        organization = self.ds.organization if organization else None

        payload = self.payload(self.ds.credential_type, user=user, team=team, organization=organization, inputs=inputs, **kwargs)
        payload.ds = DSAdapter(self.__class__.__name__, self._dependency_store)
        return payload

    def create(self, credential_type=CredentialType, user=None, team=None, organization=None, inputs=None, **kwargs):
        payload = self.create_payload(credential_type=credential_type, user=user, team=team, organization=organization, inputs=inputs, **kwargs)
        return self.update_identity(Credentials(self.connection)).post(payload)

    def test(self, data):
        """Test the credential endpoint."""
        response = self.connection.post(urljoin(str(self.url), 'test/'), data)
        exception = exception_from_status_code(response.status_code)
        exc_str = "%s (%s) received" % (http.responses[response.status_code], response.status_code)
        if exception:
            raise exception(exc_str, response.json())
        elif response.status_code == http.FORBIDDEN:
            raise exc.Forbidden(exc_str, response.json())
        return response

    @property
    def expected_passwords_needed_to_start(self):
        """Return a list of expected passwords needed to start a job using this credential."""
        passwords = []
        for field in ('password', 'become_password', 'ssh_key_unlock', 'vault_password'):
            if getattr(self.inputs, field, None) == 'ASK':
                if field == 'password':
                    passwords.append('ssh_password')
                else:
                    passwords.append(field)
        return passwords


page.register_page(
    [resources.credential, (resources.credentials, 'post'), (resources.credential_copy, 'post'), (resources.organization_galaxy_credentials, 'post')],
    Credential,
)


class Credentials(page.PageList, Credential):

    pass


page.register_page([resources.credentials, resources.related_credentials, resources.organization_galaxy_credentials], Credentials)


class CredentialCopy(base.Base):

    pass


page.register_page(resources.credential_copy, CredentialCopy)

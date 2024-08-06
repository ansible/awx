# Django
from django.utils.translation import gettext_noop

# AWX
from awx.main.models.credential import ManagedCredentialType


ManagedCredentialType(
    namespace='ssh',
    kind='ssh',
    name=gettext_noop('Machine'),
    inputs={
        'fields': [
            {'id': 'username', 'label': gettext_noop('Username'), 'type': 'string'},
            {'id': 'password', 'label': gettext_noop('Password'), 'type': 'string', 'secret': True, 'ask_at_runtime': True},
            {'id': 'ssh_key_data', 'label': gettext_noop('SSH Private Key'), 'type': 'string', 'format': 'ssh_private_key', 'secret': True, 'multiline': True},
            {
                'id': 'ssh_public_key_data',
                'label': gettext_noop('Signed SSH Certificate'),
                'type': 'string',
                'multiline': True,
                'secret': True,
            },
            {'id': 'ssh_key_unlock', 'label': gettext_noop('Private Key Passphrase'), 'type': 'string', 'secret': True, 'ask_at_runtime': True},
            {
                'id': 'become_method',
                'label': gettext_noop('Privilege Escalation Method'),
                'type': 'string',
                'help_text': gettext_noop('Specify a method for "become" operations. This is equivalent to specifying the --become-method Ansible parameter.'),
            },
            {
                'id': 'become_username',
                'label': gettext_noop('Privilege Escalation Username'),
                'type': 'string',
            },
            {'id': 'become_password', 'label': gettext_noop('Privilege Escalation Password'), 'type': 'string', 'secret': True, 'ask_at_runtime': True},
        ],
    },
)

ManagedCredentialType(
    namespace='scm',
    kind='scm',
    name=gettext_noop('Source Control'),
    managed=True,
    inputs={
        'fields': [
            {'id': 'username', 'label': gettext_noop('Username'), 'type': 'string'},
            {'id': 'password', 'label': gettext_noop('Password'), 'type': 'string', 'secret': True},
            {'id': 'ssh_key_data', 'label': gettext_noop('SCM Private Key'), 'type': 'string', 'format': 'ssh_private_key', 'secret': True, 'multiline': True},
            {'id': 'ssh_key_unlock', 'label': gettext_noop('Private Key Passphrase'), 'type': 'string', 'secret': True},
        ],
    },
)

ManagedCredentialType(
    namespace='vault',
    kind='vault',
    name=gettext_noop('Vault'),
    managed=True,
    inputs={
        'fields': [
            {'id': 'vault_password', 'label': gettext_noop('Vault Password'), 'type': 'string', 'secret': True, 'ask_at_runtime': True},
            {
                'id': 'vault_id',
                'label': gettext_noop('Vault Identifier'),
                'type': 'string',
                'format': 'vault_id',
                'help_text': gettext_noop(
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
    name=gettext_noop('Network'),
    managed=True,
    inputs={
        'fields': [
            {'id': 'username', 'label': gettext_noop('Username'), 'type': 'string'},
            {
                'id': 'password',
                'label': gettext_noop('Password'),
                'type': 'string',
                'secret': True,
            },
            {'id': 'ssh_key_data', 'label': gettext_noop('SSH Private Key'), 'type': 'string', 'format': 'ssh_private_key', 'secret': True, 'multiline': True},
            {
                'id': 'ssh_key_unlock',
                'label': gettext_noop('Private Key Passphrase'),
                'type': 'string',
                'secret': True,
            },
            {
                'id': 'authorize',
                'label': gettext_noop('Authorize'),
                'type': 'boolean',
            },
            {
                'id': 'authorize_password',
                'label': gettext_noop('Authorize Password'),
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
    name=gettext_noop('Amazon Web Services'),
    managed=True,
    inputs={
        'fields': [
            {'id': 'username', 'label': gettext_noop('Access Key'), 'type': 'string'},
            {
                'id': 'password',
                'label': gettext_noop('Secret Key'),
                'type': 'string',
                'secret': True,
            },
            {
                'id': 'security_token',
                'label': gettext_noop('STS Token'),
                'type': 'string',
                'secret': True,
                'help_text': gettext_noop(
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
    name=gettext_noop('OpenStack'),
    managed=True,
    inputs={
        'fields': [
            {'id': 'username', 'label': gettext_noop('Username'), 'type': 'string'},
            {
                'id': 'password',
                'label': gettext_noop('Password (API Key)'),
                'type': 'string',
                'secret': True,
            },
            {
                'id': 'host',
                'label': gettext_noop('Host (Authentication URL)'),
                'type': 'string',
                'help_text': gettext_noop('The host to authenticate with.  For example, https://openstack.business.com/v2.0/'),
            },
            {
                'id': 'project',
                'label': gettext_noop('Project (Tenant Name)'),
                'type': 'string',
            },
            {
                'id': 'project_domain_name',
                'label': gettext_noop('Project (Domain Name)'),
                'type': 'string',
            },
            {
                'id': 'domain',
                'label': gettext_noop('Domain Name'),
                'type': 'string',
                'help_text': gettext_noop(
                    'OpenStack domains define administrative boundaries. '
                    'It is only needed for Keystone v3 authentication '
                    'URLs. Refer to the documentation for '
                    'common scenarios.'
                ),
            },
            {
                'id': 'region',
                'label': gettext_noop('Region Name'),
                'type': 'string',
                'help_text': gettext_noop('For some cloud providers, like OVH, region must be specified'),
            },
            {
                'id': 'verify_ssl',
                'label': gettext_noop('Verify SSL'),
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
    name=gettext_noop('VMware vCenter'),
    managed=True,
    inputs={
        'fields': [
            {
                'id': 'host',
                'label': gettext_noop('VCenter Host'),
                'type': 'string',
                'help_text': gettext_noop('Enter the hostname or IP address that corresponds to your VMware vCenter.'),
            },
            {'id': 'username', 'label': gettext_noop('Username'), 'type': 'string'},
            {
                'id': 'password',
                'label': gettext_noop('Password'),
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
    name=gettext_noop('Red Hat Satellite 6'),
    managed=True,
    inputs={
        'fields': [
            {
                'id': 'host',
                'label': gettext_noop('Satellite 6 URL'),
                'type': 'string',
                'help_text': gettext_noop('Enter the URL that corresponds to your Red Hat Satellite 6 server. For example, https://satellite.example.org'),
            },
            {'id': 'username', 'label': gettext_noop('Username'), 'type': 'string'},
            {
                'id': 'password',
                'label': gettext_noop('Password'),
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
    name=gettext_noop('Google Compute Engine'),
    managed=True,
    inputs={
        'fields': [
            {
                'id': 'username',
                'label': gettext_noop('Service Account Email Address'),
                'type': 'string',
                'help_text': gettext_noop('The email address assigned to the Google Compute Engine service account.'),
            },
            {
                'id': 'project',
                'label': 'Project',
                'type': 'string',
                'help_text': gettext_noop(
                    'The Project ID is the GCE assigned identification. '
                    'It is often constructed as three words or two words '
                    'followed by a three-digit number. Examples: project-id-000 '
                    'and another-project-id'
                ),
            },
            {
                'id': 'ssh_key_data',
                'label': gettext_noop('RSA Private Key'),
                'type': 'string',
                'format': 'ssh_private_key',
                'secret': True,
                'multiline': True,
                'help_text': gettext_noop('Paste the contents of the PEM file associated with the service account email.'),
            },
        ],
        'required': ['username', 'ssh_key_data'],
    },
)

ManagedCredentialType(
    namespace='azure_rm',
    kind='cloud',
    name=gettext_noop('Microsoft Azure Resource Manager'),
    managed=True,
    inputs={
        'fields': [
            {
                'id': 'subscription',
                'label': gettext_noop('Subscription ID'),
                'type': 'string',
                'help_text': gettext_noop('Subscription ID is an Azure construct, which is mapped to a username.'),
            },
            {'id': 'username', 'label': gettext_noop('Username'), 'type': 'string'},
            {
                'id': 'password',
                'label': gettext_noop('Password'),
                'type': 'string',
                'secret': True,
            },
            {'id': 'client', 'label': gettext_noop('Client ID'), 'type': 'string'},
            {
                'id': 'secret',
                'label': gettext_noop('Client Secret'),
                'type': 'string',
                'secret': True,
            },
            {'id': 'tenant', 'label': gettext_noop('Tenant ID'), 'type': 'string'},
            {
                'id': 'cloud_environment',
                'label': gettext_noop('Azure Cloud Environment'),
                'type': 'string',
                'help_text': gettext_noop('Environment variable AZURE_CLOUD_ENVIRONMENT when using Azure GovCloud or Azure stack.'),
            },
        ],
        'required': ['subscription'],
    },
)

ManagedCredentialType(
    namespace='github_token',
    kind='token',
    name=gettext_noop('GitHub Personal Access Token'),
    managed=True,
    inputs={
        'fields': [
            {
                'id': 'token',
                'label': gettext_noop('Token'),
                'type': 'string',
                'secret': True,
                'help_text': gettext_noop('This token needs to come from your profile settings in GitHub'),
            }
        ],
        'required': ['token'],
    },
)

ManagedCredentialType(
    namespace='gitlab_token',
    kind='token',
    name=gettext_noop('GitLab Personal Access Token'),
    managed=True,
    inputs={
        'fields': [
            {
                'id': 'token',
                'label': gettext_noop('Token'),
                'type': 'string',
                'secret': True,
                'help_text': gettext_noop('This token needs to come from your profile settings in GitLab'),
            }
        ],
        'required': ['token'],
    },
)

ManagedCredentialType(
    namespace='bitbucket_dc_token',
    kind='token',
    name=gettext_noop('Bitbucket Data Center HTTP Access Token'),
    managed=True,
    inputs={
        'fields': [
            {
                'id': 'token',
                'label': gettext_noop('Token'),
                'type': 'string',
                'secret': True,
                'help_text': gettext_noop('This token needs to come from your user settings in Bitbucket'),
            }
        ],
        'required': ['token'],
    },
)

ManagedCredentialType(
    namespace='insights',
    kind='insights',
    name=gettext_noop('Insights'),
    managed=True,
    inputs={
        'fields': [
            {'id': 'username', 'label': gettext_noop('Username'), 'type': 'string'},
            {'id': 'password', 'label': gettext_noop('Password'), 'type': 'string', 'secret': True},
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
    name=gettext_noop('Red Hat Virtualization'),
    managed=True,
    inputs={
        'fields': [
            {'id': 'host', 'label': gettext_noop('Host (Authentication URL)'), 'type': 'string', 'help_text': gettext_noop('The host to authenticate with.')},
            {'id': 'username', 'label': gettext_noop('Username'), 'type': 'string'},
            {
                'id': 'password',
                'label': gettext_noop('Password'),
                'type': 'string',
                'secret': True,
            },
            {
                'id': 'ca_file',
                'label': gettext_noop('CA File'),
                'type': 'string',
                'help_text': gettext_noop('Absolute file path to the CA file to use (optional)'),
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
    namespace='controller',
    kind='cloud',
    name=gettext_noop('Red Hat Ansible Automation Platform'),
    managed=True,
    inputs={
        'fields': [
            {
                'id': 'host',
                'label': gettext_noop('Red Hat Ansible Automation Platform'),
                'type': 'string',
                'help_text': gettext_noop('Red Hat Ansible Automation Platform base URL to authenticate with.'),
            },
            {
                'id': 'username',
                'label': gettext_noop('Username'),
                'type': 'string',
                'help_text': gettext_noop(
                    'Red Hat Ansible Automation Platform username id to authenticate as.This should not be set if an OAuth token is being used.'
                ),
            },
            {
                'id': 'password',
                'label': gettext_noop('Password'),
                'type': 'string',
                'secret': True,
            },
            {
                'id': 'oauth_token',
                'label': gettext_noop('OAuth Token'),
                'type': 'string',
                'secret': True,
                'help_text': gettext_noop('An OAuth token to use to authenticate with.This should not be set if username/password are being used.'),
            },
            {'id': 'verify_ssl', 'label': gettext_noop('Verify SSL'), 'type': 'boolean', 'secret': False},
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
            'CONTROLLER_HOST': '{{host}}',
            'CONTROLLER_USERNAME': '{{username}}',
            'CONTROLLER_PASSWORD': '{{password}}',
            'CONTROLLER_VERIFY_SSL': '{{verify_ssl}}',
            'CONTROLLER_OAUTH_TOKEN': '{{oauth_token}}',
        }
    },
)

ManagedCredentialType(
    namespace='kubernetes_bearer_token',
    kind='kubernetes',
    name=gettext_noop('OpenShift or Kubernetes API Bearer Token'),
    inputs={
        'fields': [
            {
                'id': 'host',
                'label': gettext_noop('OpenShift or Kubernetes API Endpoint'),
                'type': 'string',
                'help_text': gettext_noop('The OpenShift or Kubernetes API Endpoint to authenticate with.'),
            },
            {
                'id': 'bearer_token',
                'label': gettext_noop('API authentication bearer token'),
                'type': 'string',
                'secret': True,
            },
            {
                'id': 'verify_ssl',
                'label': gettext_noop('Verify SSL'),
                'type': 'boolean',
                'default': True,
            },
            {
                'id': 'ssl_ca_cert',
                'label': gettext_noop('Certificate Authority data'),
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
    name=gettext_noop('Container Registry'),
    inputs={
        'fields': [
            {
                'id': 'host',
                'label': gettext_noop('Authentication URL'),
                'type': 'string',
                'help_text': gettext_noop('Authentication endpoint for the container registry.'),
                'default': 'quay.io',
            },
            {
                'id': 'username',
                'label': gettext_noop('Username'),
                'type': 'string',
            },
            {
                'id': 'password',
                'label': gettext_noop('Password or Token'),
                'type': 'string',
                'secret': True,
                'help_text': gettext_noop('A password or token used to authenticate with'),
            },
            {
                'id': 'verify_ssl',
                'label': gettext_noop('Verify SSL'),
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
    name=gettext_noop('Ansible Galaxy/Automation Hub API Token'),
    inputs={
        'fields': [
            {
                'id': 'url',
                'label': gettext_noop('Galaxy Server URL'),
                'type': 'string',
                'help_text': gettext_noop('The URL of the Galaxy instance to connect to.'),
            },
            {
                'id': 'auth_url',
                'label': gettext_noop('Auth Server URL'),
                'type': 'string',
                'help_text': gettext_noop('The URL of a Keycloak server token_endpoint, if using SSO auth.'),
            },
            {
                'id': 'token',
                'label': gettext_noop('API Token'),
                'type': 'string',
                'secret': True,
                'help_text': gettext_noop('A token to use for authentication against the Galaxy instance.'),
            },
        ],
        'required': ['url'],
    },
)

ManagedCredentialType(
    namespace='gpg_public_key',
    kind='cryptography',
    name=gettext_noop('GPG Public Key'),
    inputs={
        'fields': [
            {
                'id': 'gpg_public_key',
                'label': gettext_noop('GPG Public Key'),
                'type': 'string',
                'secret': True,
                'multiline': True,
                'help_text': gettext_noop('GPG Public Key used to validate content signatures.'),
            },
        ],
        'required': ['gpg_public_key'],
    },
)

ManagedCredentialType(
    namespace='terraform',
    kind='cloud',
    name=gettext_noop('Terraform backend configuration'),
    managed=True,
    inputs={
        'fields': [
            {
                'id': 'configuration',
                'label': gettext_noop('Backend configuration'),
                'type': 'string',
                'secret': True,
                'multiline': True,
                'help_text': gettext_noop('Terraform backend config as Hashicorp configuration language.'),
            },
            {
                'id': 'gce_credentials',
                'label': gettext_noop('Google Cloud Platform account credentials'),
                'type': 'string',
                'secret': True,
                'multiline': True,
                'help_text': gettext_noop('Google Cloud Platform account credentials in JSON format.'),
            },
        ],
        'required': ['configuration'],
    },
)

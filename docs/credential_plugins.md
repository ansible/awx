Credential Plugins
==================

By default, sensitive credential values (such as SSH passwords, SSH private
keys, API tokens for cloud services) in AWX are encrypted with a symmetric
encryption cipher utilizing AES-256 in CBC mode alongside a SHA-256 HMAC and
stored in the AWX database.

Alternatively, AWX supports retrieving secret values from third-party secret
management systems, such as HashiCorp Vault and Microsoft Azure Key Vault.
These external secret values will be fetched on demand every time they are
needed (generally speaking, immediately before running a playbook that needs
them).

Configuring Secret Lookups
--------------------------

When configuring AWX to pull a secret from a third party system, there are
generally three steps.

Here is an example of creating an (1) AWX Machine Credential with
a static username, `example-user` and (2) an externally sourced secret from
HashiCorp Vault Key/Value system which will populate the (3) password field on
the Machine Credential.

1.  Create the Machine Credential with a static username, `example-user`.

    ```shell
    HTTP POST https://awx.example.org/api/v2/credentials/

    {
        "organization": X,
        "credential_type": <primary_key_of_machine_credential_type>,
        "inputs": {
            "username": "example-user"
        }
    }

2.  Create a second credential used to _authenticate_ with the external
    secret management system (e.g.,, in this example, specifying a URL and an
    OAuth2.0 token _to access_ HashiCorp Vault)

    ```shell
    HTTP POST https://awx.example.org/api/v2/credentials/
    {
        "organization": X,
        "credential_type": <primary_key_of_hashicorp_vault_credential_type>,
        "inputs": {
            "url": "https://my-vault.example.org",
            "token": "some-oauth-token",
            "api_version": "v2",
        }
    }

3.  _Link_ the `password` field for the Machine credential to the external
    system by specifying the source (in this example, the HashiCorp credential)
    and metadata about the path (e.g., `/some/path/to/my/password/`).

    ```shell
    HTTP POST https://awx.example.org/api/v2/credentials/N/input_sources/
    {
        "input_field_name": "",
        "source_credential": <primary_key_of_hashicorp_vault_credential>
        "metadata": {
            "secret_path": "/path/to/my/secret/"
            "secret_field": "password"
            "secret_version": 92
        }
    }
    ```

Note that you can perform these lookups on *any* credential field - not just
the `password` field for Machine credentials.  You could just as easily create
an AWS credential and use lookups to retrieve the Access Key and Secret Key
from an external secret management system.

Writing Custom Credential Plugins
---------------------------------

Credential Plugins in AWX are just importable Python functions that are
registered using setuptools entrypoints
(https://setuptools.readthedocs.io/en/latest/setuptools.html#dynamic-discovery-of-services-and-plugins)

Example plugins officially supported in AWX can be found in the source code at
`awx.main.credential_plugins`.

Credential plugins are any Python object which defines attribute lookups for `.name`, `.inputs`, and `.backend`:

```python
import collections

CredentialPlugin = collections.namedtuple('CredentialPlugin', ['name', 'inputs', 'backend'])

def some_callable(value_from_awx, **kwargs):
    return some_libary.get_secret_key(
        url=kwargs['url'],
        token=kwargs['token'],
        key=kwargs['secret_key']
    )

some_fancy_plugin = CredentialPlugin(
    'My Plugin Name',
    # inputs will be used to create a new CredentialType() instance
    #
    # inputs.fields represents fields the user will specify *when they create*
    # a credential of this type; they generally represent fields
    # used for authentication (URL to the credential management system, any
    # fields necessary for authentication, such as an OAuth2.0 token, or
    # a username and password). They're the types of values you set up _once_
    # in AWX
    #
    # inputs.metadata represents values the user will specify *every time
    # they link two credentials together*
    # this is generally _pathing_ information about _where_ in the external
    # management system you can find the value you care about i.e.,
    #
    # "I would like Machine Credential A to retrieve its username using
    # Credential-O-Matic B at secret_key=some_key"
    inputs={
        'fields': [{
            'id': 'url',
            'label': 'Server URL',
            'type': 'string',
        }, {
            'id': 'token',
            'label': 'Authentication Token',
            'type': 'string',
            'secret': True,
        }],
        'metadata': [{
            'id': 'secret_key',
            'label': 'Secret Key',
            'type': 'string',
            'help_text': 'The value of the key in My Credential System to fetch.'
        }],
        'required': ['url', 'token', 'secret_key'],
    },
    # backend is a callable function which will be passed all of the values
    # defined in `inputs`; this function is responsible for taking the arguments,
    # interacting with the third party credential management system in question
    # using Python code, and returning the value from the third party
    # credential management system
    backend = some_callable
```

Plugins are registered by specifying an entry point in the `setuptools.setup()`
call (generally in the package's `setup.py` file - https://github.com/ansible/awx/blob/devel/setup.py):

```python
setuptools.setup(
    ...,
    entry_points = {
        ...,
        'awx.credential_plugins': [
            'fancy_plugin = awx.main.credential_plugins.fancy:some_fancy_plugin',
        ]
    }
)
```

Fetching vs. Transforming Credential Data
-----------------------------------------
While _most_ credential plugins will be used to _fetch_ secrets from external
systems, they can also be used to *transform* data from Tower _using_ an
external secret management system.  An example use case is generating signed
public keys:

```python
def my_key_signer(unsigned_value_from_awx, **kwargs):
    return some_libary.sign(
        url=kwargs['url'],
        token=kwargs['token'],
        public_data=unsigned_value_from_awx
    )
```

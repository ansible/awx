Credential Plugins
==================

By default, sensitive credential values (such as SSH passwords, SSH private
keys, API tokens for cloud services, etc.) in AWX are stored in the AWX database
after being encrypted with a symmetric encryption cipher utilizing AES-256 in
CBC mode alongside a SHA-256 HMAC.

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
a static username, `example-user` and (2) an externally-sourced secret from
HashiCorp Vault Key/Value system which will populate the (3) password field on
the Machine Credential:

1.  Create the Machine Credential with a static username, `example-user`.

2.  Create a second credential used to _authenticate_ with the external
    secret management system (in this example, specifying a URL and an
    OAuth2.0 token _to access_ HashiCorp Vault)

3.  _Link_ the `password` field for the Machine Credential to the external
    system by specifying the source (in this example, the HashiCorp Credential)
    and metadata about the path (e.g., `/some/path/to/my/password/`).

Note that you can perform these lookups on *any* field for any non-external
credential, including those with custom credential types. You could just as
easily create an AWS Credential and use lookups to retrieve the Access Key and
Secret Key from an external secret management system. External credentials
cannot have lookups applied to their fields.

Writing Custom Credential Plugins
---------------------------------

Credential Plugins in AWX are just importable Python functions that are
registered using setuptools entrypoints
(https://setuptools.readthedocs.io/en/latest/setuptools.html#dynamic-discovery-of-services-and-plugins)

Example plugins officially supported in AWX can be found in the source code at
`awx.main.credential_plugins`.

For instructions on writing and installing your own custom credential plugin, see: https://github.com/ansible/awx-custom-credential-plugin-example

Programmatic Secret Fetching
----------------------------
If you want to programmatically fetch secrets from a supported external secret
management system (for example, if you wanted to compose an AWX database connection
string in `/etc/tower/conf.d/postgres.py` using an external system rather than
storing the password in plaintext on your disk), doing so is fairly easy:

```python
from awx.main.credential_plugins import hashivault
hashivault.hashivault_kv_plugin.backend(
    url='https://hcv.example.org',
    token='some-valid-token',
    api_version='v2',
    secret_path='/path/to/secret',
    secret_key='dbpass'
)
```

```python
# Akeyless - programmatic secret fetching
from awx.main.credential_plugins import akeyless_plugin, akeyless_ssh_plugin

# KV/Static secret lookup
akeyless_plugin.backend(
    gateway_url='https://api.akeyless.io',
    access_id='your-access-id',
    access_key='your-access-key',
    secret_path='/path/to/secret',
    secret_key='dbpass',  # optional for JSON/key-value secrets
)

# SSH certificate signing
akeyless_ssh_plugin.backend(
    gateway_url='https://api.akeyless.io',
    access_id='your-access-id',
    access_key='your-access-key',
    cert_issue_name='/remote/ssh/certificate/issuer',
    cert_username='ubuntu',                   # or comma-separated list, e.g. "ubuntu,nobody"
    public_key_data='ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ...',
    ttl=600,                                  # optional
)
```

Supported Plugins
=================

HashiCorp Vault KV
------------------

AWX supports retrieving secret values from HashiCorp Vault KV
(https://www.vaultproject.io/api/secret/kv/)

The following example illustrates how to configure a Machine Credential to pull
its password from a HashiCorp Vault:

1.  Look up the ID of the Machine and HashiCorp Vault Secret Lookup Credential
    types (in this example, `1` and `15`):

```shell
~ curl -sik "https://awx.example.org/api/v2/credential_types/?name=Machine" \
    -H "Authorization: Bearer <token>"
HTTP/1.1 200 OK
{
    "results": [
        {
            "id": 1,
            "url": "/api/v2/credential_types/1/",
            "name": "Machine",
            ...
```

```shell
~ curl -sik "https://awx.example.org/api/v2/credential_types/?name__startswith=HashiCorp" \
    -H "Authorization: Bearer <token>"
HTTP/1.1 200 OK
{
    "results": [
        {
            "id": 15,
            "url": "/api/v2/credential_types/15/",
            "name": "HashiCorp Vault Secret Lookup",
            ...
```

2.  Create a Machine and a HashiCorp Vault Credential:

```shell
~ curl -sik "https://awx.example.org/api/v2/credentials/" \
    -H "Authorization: Bearer <token>" \
    -H "Content-Type: application/json" \
    -X POST \
    -d '{"user": N, "credential_type": 1, "name": "My SSH", "inputs": {"username": "example"}}'

HTTP/1.1 201 Created
{
    "credential_type": 1,
    "description": "",
    "id": 1,
    ...
```

```shell
~ curl -sik "https://awx.example.org/api/v2/credentials/" \
    -H "Authorization: Bearer <token>" \
    -H "Content-Type: application/json" \
    -X POST \
    -d '{"user": N, "credential_type": 15, "name": "My Hashi Credential", "inputs": {"url": "https://vault.example.org", "token": "vault-token", "api_version": "v2"}}'

HTTP/1.1 201 Created
{
    "credential_type": 15,
    "description": "",
    "id": 2,
    ...
```

3.  Link the Machine Credential to the HashiCorp Vault Credential:

```shell
~ curl -sik "https://awx.example.org/api/v2/credentials/1/input_sources/" \
    -H "Authorization: Bearer <token>" \
    -H "Content-Type: application/json" \
    -X POST \
    -d '{"source_credential": 2, "input_field_name": "password", "metadata": {"secret_path": "/kv/my-secret", "secret_key": "password"}}'
HTTP/1.1 201 Created
```


HashiCorp Vault SSH Secrets Engine
----------------------------------

AWX supports signing public keys via HashiCorp Vault's SSH Secrets Engine
(https://www.vaultproject.io/api/secret/ssh/)

The following example illustrates how to configure a Machine Credential to sign
a public key using HashiCorp Vault:

1.  Look up the ID of the Machine and HashiCorp Vault Signed SSH Credential
    types (in this example, `1` and `16`):

```shell
~ curl -sik "https://awx.example.org/api/v2/credential_types/?name=Machine" \
    -H "Authorization: Bearer <token>"
HTTP/1.1 200 OK
{
    "results": [
        {
            "id": 1,
            "url": "/api/v2/credential_types/1/",
            "name": "Machine",
            ...
```

```shell
~ curl -sik "https://awx.example.org/api/v2/credential_types/?name__startswith=HashiCorp" \
    -H "Authorization: Bearer <token>"
HTTP/1.1 200 OK
{
    "results": [
        {
            "id": 16,
            "url": "/api/v2/credential_types/16/",
            "name": "HashiCorp Vault Signed SSH",
```

2.  Create a Machine and a HashiCorp Vault Credential:

```shell
~ curl -sik "https://awx.example.org/api/v2/credentials/" \
    -H "Authorization: Bearer <token>" \
    -H "Content-Type: application/json" \
    -X POST \
    -d '{"user": N, "credential_type": 1, "name": "My SSH", "inputs": {"username": "example", "ssh_key_data": "RSA KEY DATA"}}'

HTTP/1.1 201 Created
{
    "credential_type": 1,
    "description": "",
    "id": 1,
    ...
```

```shell
~ curl -sik "https://awx.example.org/api/v2/credentials/" \
    -H "Authorization: Bearer <token>" \
    -H "Content-Type: application/json" \
    -X POST \
    -d '{"user": N, "credential_type": 16, "name": "My Hashi Credential", "inputs": {"url": "https://vault.example.org", "token": "vault-token"}}'

HTTP/1.1 201 Created
{
    "credential_type": 16,
    "description": "",
    "id": 2,
    ...
```

3.  Link the Machine Credential to the HashiCorp Vault Credential:

```shell
~ curl -sik "https://awx.example.org/api/v2/credentials/1/input_sources/" \
    -H "Authorization: Bearer <token>" \
    -H "Content-Type: application/json" \
    -X POST \
    -d '{"source_credential": 2, "input_field_name": "password", "metadata": {"public_key": "UNSIGNED PUBLIC KEY", "secret_path": "/ssh/", "role": "example-role"}}'
HTTP/1.1 201 Created
```

4. Associate the Machine Credential with a Job Template.  When the Job Template
   is run, AWX will use the provided HashiCorp URL and token to sign the
   unsigned public key data using the HashiCorp Vault SSH Secrets API.
   AWX will generate an `id_rsa` and `id_rsa-cert.pub` on the fly and
   apply them using `ssh-add`.


Akeyless
----------------------------

AWX supports retrieving secret values from Akeyless
(https://www.akeyless.io/)

The following example illustrates how to configure a Machine Credential to pull
its password from a Akeyless:

1.  Look up the ID of the Machine and Akeyless
    types (in this example, `1` and `17`):

```shell
~ curl -sik "https://awx.example.org/api/v2/credential_types/?name=Machine" \
    -H "Authorization: Bearer <token>"
HTTP/1.1 200 OK
{
    "results": [
        {
            "id": 1,
            "url": "/api/v2/credential_types/1/",
            "name": "Machine",
            ...
```

```shell
~ curl -sik "https://awx.example.org/api/v2/credential_types/?name__startswith=Akeyless" \
    -H "Authorization: Bearer <token>"
HTTP/1.1 200 OK
{
    "results": [
        {
            "id": 17,
            "url": "/api/v2/credential_types/17/",
            "name": "Akeyless",
            ...
```

2.  Create a Machine and an Akeyless Vault Credential:

```shell
~ curl -sik "https://awx.example.org/api/v2/credentials/" \
    -H "Authorization: Bearer <token>" \
    -H "Content-Type: application/json" \
    -X POST \
    -d '{"user": N, "credential_type": 1, "name": "My SSH", "inputs": {"username": "example"}}'

HTTP/1.1 201 Created
{
    "credential_type": 1,
    "description": "",
    "id": 1,
    ...
```

```shell
~ curl -sik "https://awx.example.org/api/v2/credentials/" \
    -H "Authorization: Bearer <token>" \
    -H "Content-Type: application/json" \
    -X POST \
    -d '{"user": N, "credential_type": 17, "name": "My Akeyless Credential", "inputs": {"gateway_url": "https://your-gateway.akeyless.io", "access_id": "your-access-id", "access_key": "your-access-key"}}'

HTTP/1.1 201 Created
{
    "credential_type": 17,
    "description": "",
    "id": 2,
    ...
```

3.  Link the Machine Credential to the Akeyless Vault Credential:

```shell
~ curl -sik "https://awx.example.org/api/v2/credentials/1/input_sources/" \
    -H "Authorization: Bearer <token>" \
    -H "Content-Type: application/json" \
    -X POST \
    -d '{"source_credential": 2, "input_field_name": "password", "metadata": {"secret_path": "/myapp/database/password", "secret_key": "password"}}'
HTTP/1.1 201 Created
```

### Akeyless Credential Fields

- **Gateway URL**: The URL of your Akeyless Gateway (e.g., https://api.akeyless.io or https://your-gateway.akeyless.io)
- **Access ID**: Your Akeyless API Access ID
- **Access Key**: Your Akeyless API Access Key (stored encrypted)
- **CA Certificate**: Optional CA certificate for TLS verification (PEM format)

### Akeyless Metadata Fields

- **Secret Path**: The path to the secret in Akeyless (e.g., /myapp/database/password)
- **Secret Key**: Optional specific key within the secret to retrieve (for JSON secrets)

### Example Usage

When using Akeyless with JSON secrets, you can specify a specific key to retrieve:

```json
{
  "secret_path": "/myapp/database",
  "secret_key": "password"
}
```

This will retrieve the `password` field from the JSON secret stored at `/myapp/database` in Akeyless.

For simple string secrets, omit the `secret_key` field:

```json
{
  "secret_path": "/myapp/api-key"
}
```

This will retrieve the entire secret value as a string.


Akeyless SSH
----------------------------

AWX supports requesting signed SSH certificates from Akeyless
(https://www.akeyless.io/). Make sure to follow the steps outlined in [Using SSH Certificates to Access Remote Machines
](https://tutorials.akeyless.io/docs/using-ssh-certificates-to-access-remote-machines).

The following example illustrates how to configure a Machine Credential to sign
an SSH public key using Akeyless:

1.  Look up the ID of the Machine and Akeyless SSH Credential
    types (in this example, `1` and `18`):

```shell
~ curl -sik "https://awx.example.org/api/v2/credential_types/?name=Machine" \
    -H "Authorization: Bearer <token>"
HTTP/1.1 200 OK
{
    "results": [
        {
            "id": 1,
            "url": "/api/v2/credential_types/1/",
            "name": "Machine",
            ...
```

```shell
~ curl -sik "https://awx.example.org/api/v2/credential_types/?name=Akeyless%20SSH" \
    -H "Authorization: Bearer <token>"
HTTP/1.1 200 OK
{
    "results": [
        {
            "id": 18,
            "url": "/api/v2/credential_types/18/",
            "name": "Akeyless SSH",
            ...
```

2.  Create a Machine and an Akeyless SSH Credential:

```shell
~ curl -sik "https://awx.example.org/api/v2/credentials/" \
    -H "Authorization: Bearer <token>" \
    -H "Content-Type: application/json" \
    -X POST \
    -d '{"user": N, "credential_type": 1, "name": "My SSH", "inputs": {"username": "example", "ssh_key_data": "RSA KEY DATA"}}'

HTTP/1.1 201 Created
{
    "credential_type": 1,
    "description": "",
    "id": 1,
    ...
```

```shell
~ curl -sik "https://awx.example.org/api/v2/credentials/" \
    -H "Authorization: Bearer <token>" \
    -H "Content-Type: application/json" \
    -X POST \
    -d '{"user": N, "credential_type": 18, "name": "My Akeyless SSH", "inputs": {"gateway_url": "https://api.akeyless.io", "access_id": "your-access-id", "access_key": "your-access-key"}}'

HTTP/1.1 201 Created
{
    "credential_type": 18,
    "description": "",
    "id": 2,
    ...
```

3.  Link the Machine Credential to the Akeyless SSH Credential:

```shell
~ curl -sik "https://awx.example.org/api/v2/credentials/1/input_sources/" \
    -H "Authorization: Bearer <token>" \
    -H "Content-Type: application/json" \
    -X POST \
    -d '{"source_credential": 2, "input_field_name": "password", "metadata": {"cert_issue_name": "/remote/ssh/certificate/issuer", "cert_username": "ubuntu", "public_key_data": "UNSIGNED PUBLIC KEY", "ttl": 600}}'
HTTP/1.1 201 Created
```

4. Associate the Machine Credential with a Job Template. When the Job Template
   is run, AWX will use the provided Akeyless gateway and credentials to request
   a signed SSH certificate using the issuer and username(s) you provide.

### Akeyless SSH Credential Fields

- **Gateway URL**: The URL of your Akeyless Gateway (e.g., https://api.akeyless.io or https://your-gateway.akeyless.io)
- **Access ID**: Your Akeyless API Access ID
- **Access Key**: Your Akeyless API Access Key (stored encrypted)
- **CA Certificate**: Optional CA certificate for TLS verification (PEM format)

### Akeyless SSH Metadata Fields

- **Certificate Issuer Name (cert_issue_name)**: Full path to the SSH certificate issuer in Akeyless (e.g., /remote/ssh/certificate/issuer)
- **Certificate Username (cert_username)**: Username(s) to embed in the certificate; comma-separated for multiple (e.g., "ubuntu,nobody")
- **Public Key Data (public_key_data)**: The SSH public key to sign (e.g., "ssh-rsa AAAA...")
- **TTL (ttl)**: Optional time-to-live in seconds for the certificate

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

AWX supports retrieving [static secrets](https://docs.akeyless.io/docs/static-secrets) and [signed SSH certificates](https://docs.akeyless.io/docs/ssh-certificates) from Akeyless used to populate AWX Machine credential fields used to enable users to log into machines using basic or SSH authentication.

### Credential Types

The Akeyless Plugin exposes 2 credential types: Akeyless and Akeyless SSH. 

**Note**: The plugin currently only supports [API Key authentication](https://docs.akeyless.io/docs/api-key).

Both credential types provide the following fields:

- **Gateway URL**: The URL of your Akeyless Gateway (e.g., https://api.akeyless.io or https://your-gateway.akeyless.io)
- **Access ID**: Your Akeyless API Access ID.
- **Access Key**: Your Akeyless API Access Key (stored encrypted).
- **(Optional) CA Certificate**: If using an Akeyless Gateway with a private/self-signed certificate, provide the CA certificate for TLS verification (PEM format).


### AWX UI: Remote Access using Basic Authentication

The following example illustrates how to SSH into a remote Ubuntu 24.04 machine using dynamically-populated user/password stored in an Akeyless password-type static secret.

#### Prerequisites

- The remote Ubuntu machine hostname is `ssh_server` and is accessible on port `22`.
- The remote Ubuntu machine has a user named `awx` with password `awx`:

    ```bash
    useradd -m -s /bin/bash awx
    echo "awx:awx" | chpasswd
    ```
- The SSH server running on the remote Ubuntu machine allows password authentication:

    ```bash
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
    sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config
    ```
- The AWX server has a mounted volume with Ansible playbooks. For example, in a Docker compose setup:

    ```yaml
    services:
      awx:
        image: "ghcr.io/ansible/awx_devel:add-akeyless-credential"
        volumes:
        - "/host/path/to/playbooks:/var/lib/awx/projects/playbooks:rw"
    ```

    Create an Ansible playbook in `/host/path/to/playbooks/demo-basic-auth-ssh.yaml` with the following:

    ```yaml
    ---
    - name: Test SSH connection to ssh_server using Akeyless credentials
        hosts: ssh_server
        gather_facts: true
        connection: ssh
        
        tasks:
        - name: Display connection information
        ansible.builtin.debug:
            msg: |
            Successfully connected to {{ inventory_hostname }}!
            User: {{ ansible_user }}
            Host: {{ ansible_host | default(inventory_hostname) }}
            OS: {{ ansible_distribution }} {{ ansible_distribution_version }}
            Architecture: {{ ansible_architecture }}

        - name: Verify we can run commands as the authenticated user
        ansible.builtin.command: whoami
        register: whoami_result
        
        - name: Display current user
        ansible.builtin.debug:
            msg: "Currently running as: {{ whoami_result.stdout }}"

        - name: Check user's home directory
        ansible.builtin.stat:
            path: "{{ ansible_env.HOME }}"
        register: home_dir
        
        - name: Display home directory information
        ansible.builtin.debug:
            msg: |
            Home directory: {{ home_dir.stat.path }}
            Home directory exists: {{ home_dir.stat.exists }}

        - name: Create a test file to verify write access
        ansible.builtin.copy:
            content: |
            This file was created by AWX using Akeyless credentials
            Timestamp: {{ ansible_date_time.iso8601 }}
            User: {{ ansible_user }}
            dest: "/home/{{ ansible_user }}/awx-test-file.txt"
            mode: '0644'
            
        - name: Verify test file was created
        ansible.builtin.command: cat /home/{{ ansible_user }}/awx-test-file.txt
        register: test_file_content
        
        - name: Display test file content
        ansible.builtin.debug:
            msg: "{{ test_file_content.stdout_lines }}"

        - name: Clean up test file
        ansible.builtin.file:
            path: "/home/{{ ansible_user }}/awx-test-file.txt"
            state: absent
    ```

#### Steps

1. [Create a new Akeyless password type static secret](https://docs.akeyless.io/docs/create-secret) named `/awx/basic-auth-test` with username `awx` and password `awx` using the Akeyless Console or CLI:

    ```bash
    AKEYLESS_PROFILE=awx-demo
    akeyless configure \
    --profile "$AKEYLESS_PROFILE" \
    --access-id "$AKEYLESS_ACCESS_ID" \
    --access-key "$AKEYLESS_ACCESS_KEY"

    akeyless create-secret \
    --name "/awx/basic-auth-test \
    --username "awx" \
    --password "awx" \
    --profile "$AKEYLESS_PROFILE"
    ```

2. In AWX, create a new Organization named `secops`.
3. In AWX, create a new Inventory named `akeyless` in Organization `secops`.
4. In AWX, create a new Project named `akeyless-test` using a **Manual** _Source control type_ and selecting the `playbooks` in the _Playbook directory_ field.
4. In AWX, create a new Host named `ssh_server` with variables inside Inventory `akeyless`:

    ```yaml
    ansible_host: ssh_server
    ansible_port: 22
    ```

5. In AWX, create a new Credential named `awx-basic-auth-test`, select `secops` Organization and select `Akeyless` in _Credential type_ field.  Fill in the _Gateway URL_, _Access ID_ and _Access Key_. Click on _Test_ and enter `/awx/basic-auth-test` in _Secret Path_, `password` in _Secret Key_ fields and click on _Run_. The test should succeed.

6. In AWX, create a new Credential named `awx-basic-auth-test` and select `Machine` in _Credential type_ field. In the _Username_ field, select the key icon (hint: Populate field from an external secret management system). In the _Secret Management System_ modal that pops up, select the `awx-basic-auth-test` credential and fill in the  `/awx/basic-auth-test` in _Secret Path_, `username` in _Secret Key_ fields. Do the same thing but for the _Password_ field but enter `password` in _Secret Key_ field.

7. In AWX, create a new Job Template named `test-static-basic-auth-retrieval`, select `secops` in _Organization_ field, select `akeyless` in _Inventory_ field, select `akeyless-test` in _Project_ field and select `demo-basic-auth-ssh.yaml` in the _Playbook_ field.

8. In AWX, launch the `test-static-basic-auth-retrieval` Job Template.


### Programmatic Access
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


Akeyless SSH
----------------------------

AWX supports requesting signed SSH certificates from Akeyless
(https://www.akeyless.io/). Make sure to follow the steps outlined in [Using SSH Certificates to Access Remote Machines
](https://tutorials.akeyless.io/docs/using-ssh-certificates-to-access-remote-machines).

### AWX UI: Remote Access using Signed SSH Certificate

The following example illustrates how to SSH into a remote Ubuntu 24.04 machine using dynamically-populated Signed SSH Certificates generated by an SSH Certificate Issuer available in Akeyless for a user `awx`.

#### Prerequisites

- The remote Ubuntu machine hostname is `ssh_server` and is accessible on port `22`.
- The remote Ubuntu machine has `openssh-server` installed and set up:

    ```bash
    apt update
    DEBIAN_FRONTEND=noninteractive apt install openssh-server -y
    mkdir -p /var/run/sshd
    /usr/sbin/sshd -D &
    ```

- The remote Ubuntu machine has an existing user named `awx`:

    ```bash
    useradd -m -s /bin/bash awx
    echo "awx:awx" | chpasswd
    mkdir -p /home/awx/.ssh
    chown awx:awx /home/awx/.ssh
    chmod 700 /home/awx/.ssh
    ```
- The AWX server has a mounted volume with Ansible playbooks. For example, in a Docker compose setup:

    ```yaml
    services:
      awx:
        image: "ghcr.io/ansible/awx_devel:add-akeyless-credential"
        volumes:
        - "/host/path/to/playbooks:/var/lib/awx/projects/playbooks:rw"
    ```

    Create an Ansible playbook in `/host/path/to/playbooks/demo-ssh-auth.yaml` with the following:

    ```yaml
    ---
    - name: Test SSH Certificate Authentication
    hosts: ssh_server
    gather_facts: false
    become: false
    
    tasks:
        - name: Test connection
        ansible.builtin.command: hostname
        register: result
        
        - name: Display result
        ansible.builtin.debug:
            msg: "Connection successful! Hostname: {{ result.stdout }}"
    ```

#### Steps

1. Create an RSA 2048 bit private key:

    ```bash
    AKEYLESS_PROFILE=awx-demo
    akeyless configure \
    --profile "$AKEYLESS_PROFILE" \
    --access-id "$AKEYLESS_ACCESS_ID" \
    --access-key "$AKEYLESS_ACCESS_KEY"

    akeyless create-key \
    --name "/awx/ssh-signing-key" \
    --alg RSA2048 \
    --profile "$AKEYLESS_PROFILE"
    ```

1. Get the RSA public key corresponding to the private key and output to a file:

    ```bash
    akeyless get-rsa-public \
    --name "/awx/ssh-signing-key" \
    --profile "$AKEYLESS_PROFILE" \
    --json | jq -r '.ssh' > /tmp/ca.pub

    cat /tmp/ca.pub
    # OUTPUT: ssh-rsa AAAAB3NzaC1...
    ```

1. Create an SSH Certificate Issuer:

    ```bash
    akeyless create-ssh-cert-issuer \
    --name "/awx/ssh-cert-issuer" \
    --signer-key-name "/awx/ssh-signing-key"  \
    --ttl 300 \
    --allowed-users 'awx' \
    --profile $AKEYLESS_PROFILE
    ```

1. Create a new private key:

    ```bash
    ssh-keygen -t rsa -b 2048 -f ~/.ssh/awx_rsa
    ```

1. In the remote Ubuntu machine, configure the SSH server to trust the signer public key and restart the SSH server:

    ```bash
    # echo the output from step 2.
    echo "ssh-rsa AAAAB3NzaC1..." > /etc/ssh/ca.pub

    cat >> /etc/ssh/sshd_config << 'EOF'
    TrustedUserCAKeys /etc/ssh/ca.pub
    PubkeyAcceptedKeyTypes=+ssh-rsa,ssh-rsa-cert-v01@openssh.com
    EOF

    service ssh restart
    ```

1. In AWX, create a new Organization named `secops`.
1. In AWX, create a new Inventory named `akeyless` in Organization `secops`.
1. In AWX, create a new Project named `akeyless-test` using a **Manual** _Source control type_ and selecting the `playbooks` in the _Playbook directory_ field.
1. In AWX, create a new Host named `ssh_server` with variables inside Inventory `akeyless`:

    ```yaml
    ansible_host: ssh_server
    ansible_port: 22
    ```

1. In AWX, create a new Credential named `awx-ssh-auth-test`, select `secops` Organization and select `Akeyless SSH` in _Credential type_ field.  Fill in the _Gateway URL_, _Access ID_ and _Access Key_. 

1. In AWX, create a new Credential named `awx-ssh-auth-test` and select `Machine` in _Credential type_ field. In the _Username_ field enter `awx`, select `secops` in _Organization_ field and select `Akeyless SSH` in _Credential type_ field. In the _Secret Management System_ modal that pops up, select the `awx-ssh-auth-test` in _Credential_ field, enter `/awx/ssh-cert-issuer` in _Certificate Issuer Name_ field, `awx` in the _Certificate Username_ field and enter the output of the public key generated in step 4, (e.g. `cat ~/.ssh/awx_rsa.pub` `ssh-rsa AAAAB3...`). In the _SSH Private Key_, enter the output of the private key generated in step 4 (e.g. cat ~/.ssh/awx_rsa, `-----BEGIN OPENSSH PRIVATE KEY-----...`).


7. In AWX, create a new Job Template named `test-ssh-auth`, select `secops` in _Organization_ field, select `akeyless` in _Inventory_ field, select `akeyless-test` in _Project_ field and select `demo-ssh-auth.yaml` in the _Playbook_ field.

8. In AWX, launch the `test-ssh-auth` Job Template.

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

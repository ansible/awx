Extracting Credential Values
============================

AWX stores a variety of secrets in the database that are either used for automation or are a result of automation. These secrets include:

- all secret fields of all credential types (passwords, secret keys, authentication tokens, secret cloud credentials)
- secret tokens and passwords for external services defined in Ansible Tower settings
- "password" type survey fields entries

To encrypt secret fields, Tower uses AES in CBC mode with a 256-bit key for encryption, PKCS7 padding, and HMAC using SHA256 for authentication.

If necessary, credentials and encrypted settings can be extracted using the AWX shell:

```python
# awx-manage shell_plus
>>> from awx.main.utils import decrypt_field
>>> cred = Credential.objects.get(name="my private key")
>>> print(decrypt_field(cred, "ssh_key_data"))
```

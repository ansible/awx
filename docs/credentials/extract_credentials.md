Extracting Credential Values
============================

AWX stores a variety of secrets in the database that are either used for automation or are a result of automation. These secrets include:

- all secret fields of all credential types (passwords, secret keys, authentication tokens, secret cloud credentials)
- secret tokens and passwords for external services defined in AWX settings
- "password" type survey fields entries

To encrypt secret fields, AWX uses AES in CBC mode with a 256-bit key for encryption, PKCS7 padding, and HMAC using SHA256 for authentication.

If necessary, credentials and encrypted settings can be extracted using the AWX shell:

```python
$ awx-manage shell_plus
>>> from awx.main.utils import decrypt_field
>>> print(decrypt_field(Credential.objects.get(name="my private key"), "ssh_key_data")) # Example for a credential
>>> print(decrypt_field(Setting.objects.get(key='SOCIAL_AUTH_AZUREAD_OAUTH2_SECRET'), 'value')) # Example for a setting
```

If you are running a kubernetes based deployment, you can execute awx-manage like this:
```bash
$ kubectl exec --stdin --tty [instance name]-task-[...] -c [instance name]-task -- awx-manage shell_plus
```
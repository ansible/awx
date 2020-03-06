Extract credentials
===================

Credentials and encrypted settings can be extracted using the following snippet:

```python
# awx-manage shell_plus
>>> from awx.main.utils import decrypt_field
>>> cred = Credential.objects.get(name="my private key")
>>> decrypt_field(cred, "ssh_key_data")
```

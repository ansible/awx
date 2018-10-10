Multi-Credential Assignment
===========================

awx has added support for assigning zero or more credentials to
JobTemplates and InventoryUpdates via a singular, unified interface.

Background
----------

Prior to awx (Tower 3.2), Job Templates had a certain set of requirements
surrounding their relation to Credentials:

* All Job Templates (and Jobs) were required to have exactly *one* Machine/SSH
  or Vault credential (or one of both).
* All Job Templates (and Jobs) could have zero or more "extra" Credentials.
* These extra Credentials represented "Cloud" and "Network" credentials that
* could be used to provide authentication to external services via environment
* variables (e.g., AWS_ACCESS_KEY_ID).

This model required a variety of disjoint interfaces for specifying Credentials
on a JobTemplate.  For example, to modify assignment of Machine/SSH and Vault
credentials, you would change the Credential key itself:

`PATCH /api/v2/job_templates/N/ {'credential': X, 'vault_credential': Y}`

Modifying `extra_credentials` was accomplished on a separate API endpoint
via association/disassociation actions:

```
POST /api/v2/job_templates/N/extra_credentials {'associate': true, 'id': Z}
POST /api/v2/job_templates/N/extra_credentials {'disassociate': true, 'id': Z}
```

This model lacked the ability associate multiple Vault credentials with
a playbook run, a use case supported by Ansible core from Ansible 2.4 onwards.

This model also was a stumbling block for certain playbook execution workflows.
For example, some users wanted to run playbooks with `connection:local` that
only interacted with some cloud service via a cloud Credential.  In this
scenario, users often generated a "dummy" Machine/SSH Credential to attach to
the Job Template simply to satisfy the requirement on the model.

Important Changes
-----------------

JobTemplates now have a single interface for Credential assignment:

`GET /api/v2/job_templates/N/credentials/`

Users can associate and disassociate credentials using `POST` requests to this
interface, similar to the behavior in the now-deprecated `extra_credentials`
endpoint:

```
POST /api/v2/job_templates/N/credentials/ {'associate': true, 'id': X'}
POST /api/v2/job_templates/N/credentials/ {'disassociate': true, 'id': Y'}
```

Under this model, a JobTemplate is considered valid even when it has _zero_
Credentials assigned to it.

Launch Time Considerations
--------------------------

Prior to this change, JobTemplates had a configurable attribute,
`ask_credential_on_launch`.  This value was used at launch time to determine
which missing credential values were necessary for launch - this was primarily
used as a mechanism for users to specify an SSH (or Vault) credential to satisfy
the minimum Credential requirement.

Under the new unified Credential list model, this attribute still exists, but it
is no longer bound to a notion of "requiring" a Credential.  Now when
`ask_credential_on_launch` is `True`, it signifies that users may (if they
wish) specify a list of credentials at launch time to override those defined on
the JobTemplate:

`POST /api/v2/job_templates/N/launch/ {'credentials': [A, B, C]}`

If `ask_credential_on_launch` is `False`, it signifies that custom `credentials`
provided in the payload to `POST /api/v2/job_templates/N/launch/` will be
ignored.

Under this model, the only purpose for `ask_credential_on_launch` is to signal
that API clients should prompt the user for (optional) changes at launch time.

Backwards Compatability Concerns
--------------------------------
A variety of API clients rely on now-deprecated mechanisms for Credential
retrieval and assignment, and those are still supported in a backwards
compatible way under this new API change.  Requests to update
`JobTemplate.credential` and `JobTemplate.vault_credential` will still behave
as they did before:

`PATCH /api/v2/job_templates/N/ {'credential': X, 'vault_credential': Y}`

If the job template (with pk=N) only has 1 vault credential,
that will be replaced with the new `Y` vault credential.

If the job template has multiple vault credentials, and these do not include
`Y`, then the new list will _only_ contain the single vault credential `Y`
specified in the deprecated request.

If the JobTemplate already has the `Y` vault credential associated with it,
then no change will take effect (the other vault credentials will not be
removed in this case). This is so that clients making deprecated requests
do not interfere with clients using the new `credentials` relation.

`GET` requests to `/api/v2/job_templates/N/` and `/api/v2/jobs/N/`
have traditionally included a variety of metadata in the response via
`related_fields`:

```
{
    "related": {
        ...
        "credential": "/api/v2/credentials/1/",
        "vault_credential": "/api/v2/credentials/3/",
        "extra_credentials": "/api/v2/job_templates/5/extra_credentials/",
    }
}
```

...and `summary_fields`:

```
{
    "summary_fields": {
        "credential": {
            "description": "",
            "credential_type_id": 1,
            "id": 1,
            "kind": "ssh",
            "name": "Demo Credential"
        },
        "vault_credential": {
            "description": "",
            "credential_type_id": 3,
            "id": 3,
            "kind": "vault",
            "name": "some-vault"
        },
        "extra_credentials": [
            {
                "description": "",
                "credential_type_id": 5,
                "id": 2,
                "kind": "aws",
                "name": "some-aws"
            },
            {
                "description": "",
                "credential_type_id": 10,
                "id": 4,
                "kind": "gce",
                "name": "some-gce"
            }
        ],
    }
}
```

These metadata will continue to exist and function in a backwards-compatible way.

The `/api/v2/job_templates/N/extra_credentials` endpoint has been deprecated, but
will also continue to exist and function in the same manner for multiple releases.

The `/api/v2/job_templates/N/launch/` endpoint also provides
deprecated,backwards compatible support for specifying credentials at launch time
via the `credential`, `vault_credential`, and `extra_credentials` fields:

`POST /api/v2/job_templates/N/launch/ {'credential': A, 'vault_credential': B, 'extra_credentials': [C, D]}`


Specifying Multiple Vault Credentials
-------------------------------------
One interesting use case supported by the new "zero or more credentials" model
is the ability to assign multiple Vault credentials to a Job Template run.

This specific use case covers Ansible's support for multiple vault passwords for
a playbook run (since Ansible 2.4):
http://docs.ansible.com/ansible/latest/vault.html#vault-ids-and-multiple-vault-passwords

Vault credentials in awx now have an optional field, `vault_id`, which is
analogous to the `--vault-id` argument to `ansible-playbook`.  To run
a playbook which makes use of multiple vault passwords:

1.  Make a Vault credential in Tower for each vault password; specify the Vault
    ID as a field on the credential and input the password (which will be
    encrypted and stored).
2.  Assign multiple vault credentials to the job template via the new
    `credentials` endpoint:

    ```
    POST /api/v2/job_templates/N/credentials/

    {
        'associate': true,
        'id': X
    }
    ```
3.  Launch the job template, and `ansible-playbook` will be invoked with
    multiple `--vault-id` arguments.

Prompted Vault Credentials
--------------------------
Vault credentials can have passwords that are marked as "Prompt on launch".
When this is the case, the launch endpoint of any related Job Templates will
communicate necessary Vault passwords via the `passwords_needed_to_start` key:

```
GET /api/v2/job_templates/N/launch/
{
    'passwords_needed_to_start': [
        'vault_password.X',
        'vault_password.Y',
    ]
}
```

...where `X` and `Y` are primary keys of the associated Vault credentials.

```
POST /api/v2/job_templates/N/launch/
{
    'credential_passwords': {
        'vault_password.X': 'first-vault-password'
        'vault_password.Y': 'second-vault-password'
    }
}
```

Inventory Source Credentials
----------------------------

Inventory sources and inventory updates that they spawn also use the same
relationship. The new endpoints for this are
 - `/api/v2/inventory_sources/N/credentials/` and
 - `/api/v2/inventory_updates/N/credentials/`

Most cloud sources will continue to adhere to the constraint that they
must have a single credential that corresponds to their cloud type.
However, this relationship allows users to associate multiple vault
credentials of different ids to inventory sources.

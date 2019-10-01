Multi-Credential Assignment
===========================

AWX has added support for assigning zero or more credentials to Job Templates and Inventory Updates via a singular, unified interface.

Background
----------

Prior to AWX (Tower 3.2), Job Templates had a certain set of requirements surrounding their relation to Credentials:

* All Job Templates (and Jobs) were required to have exactly *one* Machine/SSH
  or Vault credential (or one of both).
* All Job Templates (and Jobs) could have zero or more "extra" Credentials.
* These extra Credentials represented "Cloud" and "Network" credentials that
* Could be used to provide authentication to external services via environment
* Variables (*e.g.*, `AWS_ACCESS_KEY_ID`).

This model required a variety of disjoint interfaces for specifying Credentials on a Job Template.  For example, to modify assignment of Machine/SSH and Vault credentials, you would change the Credential key itself:

`PATCH /api/v2/job_templates/N/ {'credential': X, 'vault_credential': Y}`

Modifying `extra_credentials` was accomplished on a separate API endpoint via association/disassociation actions:

```
POST /api/v2/job_templates/N/extra_credentials {'associate': true, 'id': Z}
POST /api/v2/job_templates/N/extra_credentials {'disassociate': true, 'id': Z}
```

This model lacked the ability associate multiple Vault credentials with a playbook run, a use case supported by Ansible core from Ansible 2.4 onwards.

This model also was a stumbling block for certain playbook execution workflows.
For example, some users wanted to run playbooks with `connection:local` that
only interacted with some cloud service via a cloud Credential.  In this
scenario, users often generated a "dummy" Machine/SSH Credential to attach to
the Job Template simply to satisfy the requirement on the model.


Important Changes
-----------------

Job Templates now have a single interface for Credential assignment:

`GET /api/v2/job_templates/N/credentials/`

Users can associate and disassociate credentials using `POST` requests to this
interface, similar to the behavior in the now-deprecated `extra_credentials`
endpoint:

```
POST /api/v2/job_templates/N/credentials/ {'associate': true, 'id': X'}
POST /api/v2/job_templates/N/credentials/ {'disassociate': true, 'id': Y'}
```

Under this model, a Job Template is considered valid even when it has _zero_ Credentials assigned to it.

Launch Time Considerations
--------------------------

Prior to this change, Job Templates had a configurable attribute,
`ask_credential_on_launch`.  This value was used at launch time to determine
which missing credential values were necessary for launch - this was primarily
used as a mechanism for users to specify an SSH (or Vault) credential to satisfy
the minimum Credential requirement.

Under the new unified Credential list model, this attribute still exists, but it
is no longer bound to a notion of "requiring" a Credential.  Now when
`ask_credential_on_launch` is `True`, it signifies that users may (if they
wish) specify a list of credentials at launch time to override those defined on
the Job Template:

`POST /api/v2/job_templates/N/launch/ {'credentials': [A, B, C]}`

If `ask_credential_on_launch` is `False`, it signifies that custom `credentials`
provided in the payload to `POST /api/v2/job_templates/N/launch/` will be
ignored.

Under this model, the only purpose for `ask_credential_on_launch` is to signal
that API clients should prompt the user for (optional) changes at launch time.

Backwards Compatibility Concerns
--------------------------------
Requests to update `JobTemplate.credential` and `JobTemplate.vault_credential`
will no longer work. Example request format:

`PATCH /api/v2/job_templates/N/ {'credential': X, 'vault_credential': Y}`

This request will have no effect because support for using these
fields has been removed.

The relationship `extra_credentials` is deprecated but still supported for now.
Clients should favor the `credentials` relationship instead.

`GET` requests to `/api/v2/job_templates/N/` and `/api/v2/jobs/N/`
will include this via `related_fields`:

```
{
    "related": {
        ...
        "credentials": "/api/v2/job_templates/5/credentials/",
        "extra_credentials": "/api/v2/job_templates/5/extra_credentials/",
    }
}
```

...and `summary_fields`, which is not included in list views:

```
{
    "summary_fields": {
        "credentials": [
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

The only difference between `credentials` and `extra_credentials` is that the
latter is filtered to only show "cloud" type credentials, whereas the former
can be used to manage all types of related credentials.

The `/api/v2/job_templates/N/launch/` endpoint no longer provides
backwards compatible support for specifying credentials at launch time
via the `credential` or `vault_credential` fields.
The launch endpoint can still accept a list under the `extra_credentials` key,
but this is deprecated in favor `credentials`.


Specifying Multiple Vault Credentials
-------------------------------------
One interesting use case supported by the new "zero or more credentials" model
is the ability to assign multiple Vault credentials to a Job Template run.

This specific use case covers Ansible's support for multiple Vault passwords for
a playbook run (since Ansible 2.4):
http://docs.ansible.com/ansible/latest/vault.html#vault-ids-and-multiple-vault-passwords

Vault credentials in AWX now have an optional field, `vault_id`, which is
analogous to the `--vault-id` argument to `ansible-playbook`.  To run
a playbook which makes use of multiple Vault passwords:

1.  Make a Vault credential in Tower for each Vault password; specify the Vault
    ID as a field on the credential and input the password (which will be
    encrypted and stored).
2.  Assign multiple Vault credentials to the job template via the new
    `credentials` endpoint:

    ```
    POST /api/v2/job_templates/N/credentials/

    {
        'associate': true,
        'id': X
    }
    ```
3.  Launch the Job Template, and `ansible-playbook` will be invoked with
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
relationship. The new endpoints for this are:
 - `/api/v2/inventory_sources/N/credentials/` and
 - `/api/v2/inventory_updates/N/credentials/`

Most cloud sources will continue to adhere to the constraint that they
must have a single credential that corresponds to their cloud type.
However, this relationship allows users to associate multiple vault
credentials of different IDs to inventory sources.

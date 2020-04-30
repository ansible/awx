Custom Credential Types Overview
================================

Prior to Tower 3.2, Tower included bundled credential types, such as
"Machine", "Network", or "Amazon Web Services".  In 3.2, we have added support
for custom types so that customers can extend Tower with support for
third-party credential mechanisms.

Important Changes
-----------------
* Tower has a new top-level resource, ``Credential Type``, which can fall into
  one of several categories, or "kinds":

    - SSH
    - Vault
    - Source Control
    - Network
    - Cloud

  ``Credential Types`` are composed of a set of field ``inputs`` (for example,
  ``"username"`` - which is a required string - and ``"password"`` - which is
  a required string which should be encrypted at storage time) and custom
  ``injectors`` which define how the inputs are applied to the environment when
  a job is run (for example, the value for ``"username"`` should be injected
  into an environment variable named ``"MY_USERNAME"``).

  By utilizing these custom ``Credential Types``, customers have the ability to
  define custom "Cloud" and "Network" ``Credential Types`` which
  modify environment variables, extra vars, and generate file-based
  credentials (such as file-based certificates or `.ini` files) at
  `ansible-playbook` runtime.

* Multiple ``Credentials`` can now be assigned to a ``Job Template`` as long as
  the ``Credential Types`` are unique.  For example, you can now create a ``Job
  Template`` that uses one SSH, one Vault, one EC2, and one Google Compute
  Engine credential.  You cannot, however, create a ``Job Template`` that uses
  two OpenStack credentials.

* In the same manner as "promptable SSH credentials", when
  ``ask_credential_on_launch = true``, ``JobTemplate.credentials`` can be
  specified in the launch payload.

* Custom inventory sources can now utilize a ``Credential``; you
  can store third-party credentials encrypted within Tower and use their
  values from within your custom inventory script (by - for example - reading
  an environment variable or a file's contents).

API Interaction for Credential Management
-----------------------------------------

``HTTP GET /api/v2/credential_types`` provides a listing of all supported
``Credential Types``, including several read-only types that Tower provides
support for out of the box (SSH, Vault, SCM, Network, Amazon Web Services,
etc...)

Superusers have the ability to extend Tower by creating, updating, and deleting
new "custom" ``Credential Types``:

    HTTP POST /api/v2/credential_types/

    {
        "name": "Third Party Cloud",
        "description": "Integration with Third Party Cloud",
        "kind": "cloud",
        "inputs": {
            "fields": [{
                "id": "api_token",
                "label": "API Token",
                "type": "string",
                "secret": true
            }]
        },
        "injectors": {
            "env": {
                "THIRD_PARTY_CLOUD_API_TOKEN": "{{api_token}}"
            }
        }
    }

In Tower 3.2, when users create or modify ``Credentials``, they specify the
``credential_type``, and the inputs they pass in are dictated by the
defined ``inputs`` for that ``Credential Type``:

    HTTP POST /api/v2/credentials/

    {
        "name": "Joe's Third Party Cloud API Token",
        "description": "",
        "organization": <pk>,
        "user": null,
        "team": null,
        "credential_type": <pk>,
        "inputs": {
            "api_token": "f239248b-97d0-431b-ae2f-091d80c3452e"
        }
    }

    HTTP GET /api/v2/credentials/N

    {
        "name": "Joe's Third Party Cloud API Token",
        "description": "",
        "organization": <pk>,
        "user": null,
        "team": null,
        "credential_type": <pk>,
        "inputs": {
            "api_token": "$encrypted$"
        }
    }

Defining Custom Credential Type Inputs
--------------------------------------

A ``Credential Type`` specifies an ``inputs`` schema which defines a set of
ordered fields for that type:

    "inputs": {
        "fields": [{
            "id": "api_token",               # required - a unique name used to
                                             # reference the field value

            "label": "API Token",            # required - a unique label for the
                                             # field

            "help_text": "User-facing short text describing the field.",

            "type": ("string" | "boolean")   # defaults to 'string'

            "format": "ssh_private_key"      # optional, can be used to enforce data
                                             # format validity for SSH private key
                                             # data (only applicable to `type=string`)

            "secret": true,                  # if true, the field value will be encrypted

            "multiline": false               # if true, the field should be rendered
                                             # as multi-line for input entry
                                             # (only applicable to `type=string`)

            "default": "default value"       # optional, can be used to provide a
                                             # default value if the field is left empty;
                                             # when creating a credential of this type,
                                             # credential forms will use this value
                                             # as a prefill when making credentials of
                                             # this type
        },{
            # field 2...
        },{
            # field 3...
        }]
        "required": ["api_token"]            # optional; one or more fields can be marked as required
    },

When `type=string`, fields can optionally specify multiple choice options:

    "inputs": {
        "fields": [{
            "id": "api_token",          # required - a unique name used to reference the field value
            "label": "API Token",       # required - a unique label for the field
            "type": "string",
            "choices": ["A", "B", "C"]
        }]
    },

Defining Custom Credential Type Injectors
-----------------------------------------
A ``Credential Type`` can inject ``Credential`` values through the use
of the [Jinja templating language](https://jinja.palletsprojects.com/en/2.10.x/) (which should be familiar to users of Ansible):

    "injectors": {
        "env": {
            "THIRD_PARTY_CLOUD_API_TOKEN": "{{api_token}}"
        },
        "extra_vars": {
            "some_extra_var": "{{username}}:{{password}"
        }
    }

``Credential Types`` can also generate temporary files to support `.ini` files or
certificate/key data:

    "injectors": {
        "file": {
            "template": "[mycloud]\ntoken={{api_token}}"
        },
        "env": {
            "MY_CLOUD_INI_FILE": "{{tower.filename}}"
        }
    }

3.3 adds the ability for a single ``Credential Type`` to inject multiple files:

    "injectors": {
        "file": {
            "template.cert": "{{cert}}",
            "template.key": "{{key}}"
        },
        "env": {
            "MY_CERT": "{{tower.filename.cert}",
            "MY_KEY": "{{tower.filename.key}}"
        }
    }

Note that the single and multi-file syntax cannot be mixed within the same
``Credential Type``.

Job and Job Template Credential Assignment
------------------------------------------

In Tower 3.2, ``Jobs`` and ``Job Templates`` have a new many-to-many
relationship with ``Credential`` that allows selection of multiple
network/cloud credentials.  As such, the ``Job`` and ``JobTemplate``
API resources in `/api/v2/` now have two credential related fields:

    HTTP GET /api/v2/job_templates/N/

    {
      ...
      'credential': <integer-or-null>
      'vault_credential': <integer-or-null>
      ...
    }

...and a new endpoint for fetching all credentials:

    HTTP GET /api/v2/job_templates/N/credentials/

    {
        'count': N,
        'results': [{
            'name': 'My Credential',
            'credential_type': <pk>,
            'inputs': {...},
            ...
        }]
    }

Similar to other list attachment/detachment API views, cloud and network
credentials can be created and attached via an `HTTP POST` at this new
endpoint:

    HTTP POST /api/v2/job_templates/N/credentials/

    {
        'id': <cloud_credential_primary_key>,
        'associate': True,
    }

    HTTP POST /api/v2/job_templates/N/credentials/

    {
        'id': <network_credential_primary_key>,
        'disassociate': True,
    }

    HTTP POST /api/v2/job_templates/N/credentials/

    {
        'name': 'My Credential',
        'credential_type': <primary_key>,
        'inputs': {...},
        ...
    }


Additional Criteria
-------------------
* Rackspace is being removed from official support in Tower 3.2.  Pre-existing
  Rackspace Cloud credentials should be automatically migrated to "custom"
  credentials.  If a customer has never created or used Rackspace Cloud
  credentials, the only change they should notice in Tower 3.2 is that
  Rackspace is no longer an option provided by Tower when creating/modifying
  a Credential.


Acceptance Criteria
-------------------
When verifying acceptance, the following statements should be true:

* `Credential` injection for playbook runs, SCM updates, inventory updates, and
  ad-hoc runs should continue to function as they did prior to Tower 3.2 for the
  `Credential Types` provided by Tower.
* It should be possible to create and modify every type of `Credential` supported
  prior to Tower 3.2 (SSH, SCM, EC2, etc..., with the exception of Rackspace).
* Superusers (and only superusers) should be able to define custom `Credential
  Types`.  They should properly inject environment variables, extra vars, and
  files for playbook runs, SCM updates, inventory updates, and ad-hoc runs.
* Custom `Credential Types` should support injecting both single and
  multiple files. (Furthermore, the new syntax for injecting multiple files
  should work properly even if only a single file is injected).
* Users should not be able to use the syntax for injecting single and
  multiple files in the same custom credential.
* The default `Credential Types` included with Tower in 3.2 should be
  non-editable/read-only and unable to be deleted by any user.
* Stored `Credential` values for _all_ types should be consistent before and
  after a Tower 3.2 migration/upgrade.
* `Job Templates` should be able to specify multiple extra `Credentials` as
  defined in the constraints in this document.
* Custom inventory sources should be able to specify a cloud/network
  `Credential` and they should properly update the environment (environment
  variables, extra vars, written files) when an inventory source update runs.
* If a `Credential Type` is being used by one or more `Credentials`, the fields
  defined in its `inputs` should be read-only.
* `Credential Types` should support Activity Stream history for basic object
  modification.

# Credentials & Credential Types: Integration Surface Area

## Question
What is the surface area of credentials and credential types integration?

## Summary

Credentials in AWX span three core models, ~15 API endpoint groups, a plugin-based injection system, symmetric encryption, and RBAC. The integration surface is deep: credentials are consumed by jobs, project syncs, inventory syncs, and organizations—and they can pull secret values dynamically from external backends at runtime.

---

## 1. Models

**File:** `awx/main/models/credential.py`

### `Credential`
- `credential_type` (FK to CredentialType)
- `inputs` (CredentialInputField) — encrypted dict of secret/non-secret values
- `organization` (FK) — ownership
- `managed` (bool) — system-managed flag
- `admin_role`, `use_role`, `read_role` (ImplicitRoleField) — RBAC
- `input_sources` (reverse FK to CredentialInputSource) — dynamic value injection

Key methods:
- `get_input(field_name)` — decrypt and return a field value
- `has_input(field_name)` — check presence
- `display_inputs()` — mask secrets as `$encrypted$`
- `unique_hash()` — identity key (used for Vault credential deduplication)

### `CredentialType`
- `kind` — one of: `ssh`, `vault`, `net`, `scm`, `cloud`, `registry`, `token`, `insights`, `external`, `kubernetes`, `galaxy`, `cryptography`
- `namespace` — unique identifier for managed/external types
- `managed` (bool) — true for built-in types
- `inputs` (CredentialTypeInputField) — JSON schema of input fields
- `injectors` (CredentialTypeInjectorField) — env/file/extra_vars injection config
- `plugin` — reference to external backend (for `external` kind)

Key methods:
- `inject_credential(credential, env, safe_env, args, private_data_dir)` — performs injection
- `setup_tower_managed_defaults()` — registers built-in types from entry points
- `load_plugin(namespace, plugin)` — registers an external credential plugin

Key properties:
- `defined_fields`, `secret_fields`, `askable_fields`

### `CredentialInputSource`
Links an external credential to a target credential field.
- `target_credential` (FK to Credential)
- `source_credential` (FK to Credential, must be `external` kind)
- `input_field_name` — which field of target to populate
- `metadata` (DynamicCredentialInputField) — backend-specific config (e.g., JWT audience)

Key method:
- `get_input_value(context)` — calls external backend to retrieve the value at runtime

### `ManagedCredentialType`
A `SimpleNamespace` registry (`ManagedCredentialType.registry`) of all managed/external type definitions, discovered via `load_credentials()` from entry points:
- `awx_plugins.managed_credentials`
- `awx_plugins.managed_credentials.supported` (AAP only)
- `awx_plugins.credentials` (external backends)

---

## 2. Fields

**File:** `awx/main/fields.py`

| Field Class | Purpose |
|---|---|
| `CredentialInputField` | Validates `credential.inputs` against type schema; handles encryption, `$encrypted$` sentinel, SSH key checks, field dependencies |
| `CredentialTypeInputField` | Validates `credential_type.inputs` JSON schema: field IDs, types (string/boolean), secret, ask_at_runtime, format (ssh_private_key/url), choices |
| `CredentialTypeInjectorField` | Validates `credential_type.injectors`: env vars, file templates (`template.*`), extra_vars with Jinja2; blocks ANSIBLE_* and blocklisted vars |
| `DynamicCredentialInputField` | Arbitrary JSON for `CredentialInputSource.metadata` |

---

## 3. Encryption

**File:** `awx/main/utils/encryption.py`

- Algorithm: Fernet256 (AES-256-CBC) via `cryptography` library
- Key derivation: `SECRET_KEY + field_name + instance.pk` (per-field, per-instance)
- Wire format: `$encrypted$UTF8$AESCBC$<base64>`
- Functions: `encrypt_field`, `decrypt_field`, `encrypt_value`, `decrypt_value`, `get_encryption_key`
- Key rotation: `awx-manage regenerate_secret_key`

All fields listed in `CredentialType.secret_fields` are encrypted on write and decrypted on read. API responses display `$encrypted$` in place of secret values.

---

## 4. API Endpoints

**Files:** `awx/api/urls/credential*.py`, `awx/api/views/__init__.py`

### Credential Types
| Method | URL | View |
|---|---|---|
| GET/POST | `/api/v2/credential_types/` | `CredentialTypeList` |
| GET/PUT/PATCH/DELETE | `/api/v2/credential_types/{id}/` | `CredentialTypeDetail` |
| GET/POST | `/api/v2/credential_types/{id}/credentials/` | `CredentialTypeCredentialList` |
| GET | `/api/v2/credential_types/{id}/activity_stream/` | `CredentialTypeActivityStreamList` |
| POST | `/api/v2/credential_types/{id}/test/` | `CredentialTypeExternalTest` |

### Credentials
| Method | URL | View |
|---|---|---|
| GET/POST | `/api/v2/credentials/` | `CredentialList` |
| GET/PUT/PATCH/DELETE | `/api/v2/credentials/{id}/` | `CredentialDetail` |
| GET | `/api/v2/credentials/{id}/activity_stream/` | `CredentialActivityStreamList` |
| GET | `/api/v2/credentials/{id}/access_list/` | `CredentialAccessList` |
| GET | `/api/v2/credentials/{id}/owner_users/` | `CredentialOwnerUsersList` |
| GET | `/api/v2/credentials/{id}/owner_teams/` | `CredentialOwnerTeamsList` |
| POST | `/api/v2/credentials/{id}/copy/` | `CredentialCopy` |
| GET/POST | `/api/v2/credentials/{id}/input_sources/` | `CredentialInputSourceSubList` |
| POST | `/api/v2/credentials/{id}/test/` | `CredentialExternalTest` |

### Credential Input Sources
| Method | URL | View |
|---|---|---|
| GET/POST | `/api/v2/credential_input_sources/` | `CredentialInputSourceList` |
| GET/PUT/PATCH/DELETE | `/api/v2/credential_input_sources/{id}/` | `CredentialInputSourceDetail` |

### Sub-endpoints (credentials attached to other resources)
- `/api/v2/jobs/{id}/credentials/`
- `/api/v2/job_templates/{id}/credentials/`
- `/api/v2/users/{id}/credentials/`
- `/api/v2/teams/{id}/credentials/`
- `/api/v2/organizations/{id}/credentials/`

---

## 5. Serializers

**File:** `awx/api/serializers.py` (~lines 2887–3150)

| Serializer | Notes |
|---|---|
| `CredentialTypeSerializer` | Validates managed types can't be modified; restricts custom kinds to `cloud`/`net` |
| `CredentialSerializer` | Masks secrets; validates type can't change if in use |
| `CredentialSerializerCreate` | Adds ownership fields (user/team/org); calls `give_creator_permissions()` |
| `UserCredentialSerializerCreate` | For `/users/{id}/credentials/` |
| `TeamCredentialSerializerCreate` | For `/teams/{id}/credentials/` |
| `OrganizationCredentialSerializerCreate` | For `/organizations/{id}/credentials/` |
| `CredentialInputSourceSerializer` | Validates source must be `external` kind; validates target/source pairing |

---

## 6. Views

**File:** `awx/api/views/__init__.py` (~lines 1393–1701)

- `CredentialTypeList/Detail` — prevents deleting managed or in-use types
- `CredentialList/Detail` — prevents deleting managed credentials
- `CredentialCopy` — deep copy with name override
- `CredentialExternalTest` / `CredentialTypeExternalTest` — invoke external backend without saving; used for UI "test" button

---

## 7. Job Execution Integration

**File:** `awx/main/tasks/jobs.py`

### Credential Lifecycle in Jobs
1. **Loading:** `build_credentials_list(instance)` overridden per job type; result cached as `_credentials`
2. **Typed accessors:** `_machine_credential`, `_vault_credentials`, `_cloud_credentials`, `_network_credentials`
3. **Dynamic token population:** `populate_workload_identity_tokens()` — generates JWT tokens for OIDC-backed external credentials; stored in `credential.context` keyed by `input_source.pk`; requires `FEATURE_OIDC_WORKLOAD_IDENTITY_ENABLED`
4. **Injection:** For each credential:
   ```python
   credential.credential_type.inject_credential(
       credential, env, self.safe_cred_env, args, private_data_dir
   )
   ```
   Delegates to `awx_plugins.interfaces._temporary_private_inject_api.inject_credential()`
5. **Private data:** `build_private_data()` decrypts SSH keys/certs and writes them to temp files
6. **Password prompting:** `passwords_needed` property aggregates prompted fields; `build_passwords()` collects them at launch

### Injection Vectors
| Vector | Mechanism |
|---|---|
| `env` | Environment variables set in job subprocess |
| `file` | Jinja2-templated files written to `private_data_dir`; path available as env var |
| `extra_vars` | Jinja2-templated variables appended to ansible-playbook invocation |

---

## 8. RBAC

Three implicit roles on `Credential`:

| Role | Grants | Inherits from |
|---|---|---|
| `admin_role` | Full modify/delete | `system.administrator`, `organization.credential_admin_role` |
| `use_role` | Use in jobs/templates | `admin_role` |
| `read_role` | View credential | `system.auditor`, `organization.auditor_role`, `use_role` |

Custom permission: `use_credential` enforced when attaching credentials to job templates/jobs.

Credentials must belong to the same organization as the job template that uses them (or be unowned).

---

## 9. Related Model Connections

| Model | Relation | Notes |
|---|---|---|
| `UnifiedJobTemplate` | `credentials` (M2M) | Job templates, workflow nodes |
| `UnifiedJob` | `credentials` (M2M) | Job instances |
| `Organization` | `galaxy_credentials` (ordered M2M) | Galaxy/Automation Hub access |
| `InventorySource` | `credentials` (M2M) | Dynamic inventory sync |
| Project | SCM credential (FK via JobTemplate) | Source code checkout |

---

## 10. Built-in Managed Credential Types

Registered via `awx_plugins.managed_credentials` entry points:

| Kind | Examples |
|---|---|
| `ssh` (Machine) | username, password, ssh_key_data, ssh_key_unlock, become_* |
| `vault` | vault_password, vault_id |
| `net` (Network) | username, password, authorize, authorize_password, host, secret |
| `scm` | username, password, ssh_key_data |
| `cloud` | AWS (access_key/secret_key), Azure RM, GCP, OpenStack, VMware |
| `registry` | registry_url, username, password |
| `kubernetes` | host, bearer_token, ssl_ca_cert |
| `galaxy` | url, auth_url, token |
| `external` | CyberArk AIM/Conjur, HashiCorp Vault (KV/SSH/TOTP), AWS Secrets Manager, Azure Key Vault, Centrify, Thycotic, GitHub App |

Custom credential types are user-created and restricted to `cloud` or `net` kinds.

---

## 11. Collection Integration

**Directory:** `awx_collection/plugins/modules/`

| Module | Operations |
|---|---|
| `credential.py` | CRUD via `name`, `credential_type`, `inputs`, `organization`/`user`/`team`; `update_secrets` flag |
| `credential_type.py` | CRUD for custom types with `kind`, `inputs`, `injectors` |
| `credential_input_source.py` | Link external credentials to target fields |

**Tests:** `awx_collection/test/awx/test_credential*.py`

---

## 12. Test Locations

| File | Coverage |
|---|---|
| `awx/main/tests/functional/api/test_credential.py` | CRUD, ownership, encryption, validation (~1364 lines) |
| `awx/main/tests/functional/api/test_credential_type.py` | Type CRUD, injection schema (~476 lines) |
| `awx/main/tests/functional/api/test_credential_input_sources.py` | External credential integration (~377 lines) |
| `awx/main/tests/functional/rbac/test_rbac_credential.py` | Role-based access control |
| `awx/main/tests/unit/models/test_credential.py` | Unit tests for model methods |
| `awx/main/tests/functional/api/test_deprecated_credential_assignment.py` | Legacy assignment behavior |

---

## Key Architectural Patterns

### Dynamic Input Resolution
1. Static inputs: stored encrypted in `credential.inputs`
2. Dynamic inputs: fetched at job launch via `CredentialInputSource.get_input_value()` → external backend call
3. OIDC tokens: generated by `populate_workload_identity_tokens()` and cached in `credential.context`

### Plugin System
- External credential types implement a backend callable
- Registered via `awx_plugins.credentials` entry point
- Called with credential inputs + metadata; returns dict of field values
- Enables integration with CyberArk, HashiCorp Vault, AWS Secrets Manager, etc.

### Managed vs Custom vs External
| Type | `managed` | `kind` | Can modify? | Backend? |
|---|---|---|---|---|
| Managed (built-in) | True | any | No | No (injector-based) |
| External (built-in) | True | `external` | No | Yes (plugin callable) |
| Custom (user-created) | False | `cloud`/`net` | Yes | No |

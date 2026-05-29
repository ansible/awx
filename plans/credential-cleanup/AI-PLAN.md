# Credential Cleanup: Residual Coupling Analysis & Plan

## Context

Credential types have been externalized via the `inject_credential()` interface
(delegated to `awx_plugins.interfaces._temporary_private_inject_api`). However,
significant residual coupling to specific credential kinds remains throughout the
AWX codebase. This plan identifies each coupling site and proposes how to remove it.

---

## Coupling Inventory

### 1. `Credential` model — SSH/vault/cloud-specific properties
**File:** `awx/main/models/credential.py:178-243`

The `Credential` model exposes properties that hard-code `credential_type.kind`
comparisons for specific built-in kinds:

| Property | Kind hardcoded | Lines |
|---|---|---|
| `kind` | (re-exposes `namespace`) | 178-179 |
| `cloud` | `'cloud'` | 182-183 |
| `kubernetes` | `'kubernetes'` | 186-187 |
| `needs_ssh_password` | `'ssh'` | 199-200 |
| `needs_ssh_key_unlock` | `'ssh'` | 219-222 |
| `needs_become_password` | `'ssh'` | 225-226 |
| `needs_vault_password` | `'vault'` | 229-230 |
| `passwords_needed` | (calls the above) | 232-243 |
| `unique_hash` | `'vault'` (vault_id special case) | 312-328 |

**Problem:** Every credential type that needs "ask at runtime" behavior must be
`kind='ssh'` or `kind='vault'`. The vault_id multi-instance exemption is also
baked in here.

**Proposed fix:** Move `needs_*` logic into the plugin/credential-type layer.
`CredentialType` (or a mixin on `ManagedCredentialType`) should declare askable
password fields and their conditions. The `Credential` model delegates to
`self.credential_type.get_passwords_needed(self)` rather than branching on kind.

---

### 2. `JobOptions` model — kind-based credential accessors
**File:** `awx/main/models/jobs.py:167-180`

```python
@property
def machine_credential(self):
    return self.credentials.filter(credential_type__kind='ssh').first()

@property
def network_credentials(self):
    return list(self.credentials.filter(credential_type__kind='net'))

@property
def cloud_credentials(self):
    return list(self.credentials.filter(credential_type__kind='cloud'))

@property
def vault_credentials(self):
    return list(self.credentials.filter(credential_type__kind='vault'))
```

**Problem:** These properties are used extensively in tests and serializers.
They lock the model to a specific set of known kinds.

**Proposed fix:** These are convenience accessors and may be acceptable to
retain as-is if they are only used for display/serialization. However, any
behavioral dispatch that uses them should be eliminated. Consider renaming to
make the kind-coupling explicit (`credentials_of_kind('ssh')`) or removing once
callers are cleaned up.

---

### 3. `RunJob` task — kind-based credential dispatch
**File:** `awx/main/tasks/jobs.py:1004-1025, 1116-1133`

#### a) Kind-based credential extraction (lines 1004-1025)
```python
def _extract_credentials_of_kind(self, kind: str):
    return (cred for cred in self._credentials if cred.credential_type.kind == kind)

@property
def _machine_credential(self):
    return next(self._extract_credentials_of_kind('ssh'), None)

@property
def _vault_credentials(self):
    return list(self._extract_credentials_of_kind('vault'))

@property
def _network_credentials(self):
    return list(self._extract_credentials_of_kind('net'))

@property
def _cloud_credentials(self):
    return list(self._extract_credentials_of_kind('cloud'))
```

#### b) Network credential env injection NOT delegated to `inject_credential` (lines 1122-1133)
```python
for network_cred in self._network_credentials:
    env['ANSIBLE_NET_USERNAME'] = network_cred.get_input('username', default='')
    env['ANSIBLE_NET_PASSWORD'] = network_cred.get_input('password', default='')
    ...
    env['ANSIBLE_NET_AUTHORIZE'] = str(int(authorize))
```
This is a manual injection that bypasses `inject_credential()` entirely.

#### c) OpenStack namespace special-case (line 1119)
```python
if cloud_cred and cloud_cred.credential_type.namespace == 'openstack' and cred_files.get(cloud_cred, ''):
    env['OS_CLIENT_CONFIG_FILE'] = get_incontainer_path(...)
```
OpenStack requires a special env var that references a credential file path.
This is not handled by the OpenStack plugin's injector.

#### d) SSH/SCM key pipe vs disk decision (line 418)
```python
if credential and credential.credential_type.namespace in ('ssh', 'scm'):
    ssh_key_data = data
```
Whether a key is passed via ssh-agent pipe or written to disk depends on
the namespace being 'ssh' or 'scm'. This is runner-level integration logic
that cannot easily be delegated to the credential plugin.

**Proposed fix:**
- Network credential injection (b) should be moved into the network credential
  type's injector in `awx_plugins`. This is the clearest violation of the
  `inject_credential()` contract.
- OpenStack file path injection (c) should be handled by the OpenStack plugin's
  injector, which currently cannot reference the file written by `build_private_data`.
  Requires a runner-aware injection hook or passing `cred_files` into the injection
  call.
- SSH/SCM pipe decision (d) is likely acceptable as runner-integration glue
  that lives outside the injection abstraction.

---

### 4. `InventorySourceOptions` — kind-based credential validation
**File:** `awx/main/models/inventory.py:1036-1054, 1190`

```python
elif source == 'custom' and cred and cred.credential_type.kind in ('scm', 'ssh', 'insights', 'vault'):
    return _('Credentials of type machine, source control, insights and vault are disallowed...')
elif source == 'scm' and cred and cred.credential_type.kind in ('insights', 'vault'):
    return _('Credentials of type insights and vault are disallowed...')
elif source == 'openshift_virtualization' and cred and cred.credential_type.kind != 'kubernetes':
    return _('Credentials of type kubernetes is required...')
...
if cred.credential_type.kind != 'vault':
    credential = cred
```

And at line 1190:
```python
return bool(credential and credential.kind == 'gce')
```

**Problem:** Inventory source validation hard-codes which credential kinds are
disallowed or required per source type.

**Proposed fix:** Introduce a `CredentialType.compatible_inventory_sources`
attribute (list of allowed sources, or `None` for all) and a
`CredentialType.incompatible_inventory_sources` attribute. The validation logic
queries these rather than hard-coding kind names. Alternatively, move the
validation into the inventory source plugin layer.

---

### 5. `CredentialType.KIND_CHOICES` — enumerated kind field
**File:** `awx/main/models/credential.py:429-442`

```python
KIND_CHOICES = (
    ('ssh', _('Machine')),
    ('vault', _('Vault')),
    ('net', _('Network')),
    ('scm', _('Source Control')),
    ('cloud', _('Cloud')),
    ('registry', _('Container Registry')),
    ('token', _('Personal Access Token')),
    ('insights', _('Insights')),
    ('external', _('External')),
    ('kubernetes', _('Kubernetes')),
    ('galaxy', _('Galaxy/Automation Hub')),
    ('cryptography', _('Cryptography')),
)
```

**Problem:** The `kind` field is a closed enum on the database model. Adding a
new credential family requires a migration. All the behavioral branching above
is driven by this enum.

**Proposed fix:** Long-term, `kind` should become a grouping/display hint only,
with no behavioral dispatch. Short-term, ensure no new behavioral branches on
`kind` are introduced.

---

### 6. API serializers — kind-based validation and summary fields
**File:** `awx/api/serializers.py:168-189, 2586, 3048, 3390, 3482, 4658-4665`

- Summary fields expose `kind`, `cloud`, `kubernetes` for display (acceptable)
- Line 3048: Special-case vault inputs validation
- Lines 4664-4665: Whitelist of allowed kinds for job template credentials:
  ```python
  if cred.credential_type.kind not in ('ssh', 'vault', 'cloud', 'net', 'kubernetes'):
      errors.append('Cannot assign a Credential of kind `{}`')
  ```

**Problem:** The credential assignment whitelist means new credential kinds
cannot be assigned to job templates without editing the serializer.

**Proposed fix:** Replace the whitelist with an attribute on `CredentialType`:
`assignable_to_job_template = True/False`. Managed types set this in their
`ManagedCredentialType` definition. Custom types default to `True`.

---

### 7. API views — `JobTemplateCredentialsList` kind whitelist
**File:** `awx/api/views/__init__.py:2850-2852`

```python
kind = sub.credential_type.kind
if kind not in ('ssh', 'vault', 'cloud', 'net', 'kubernetes'):
    return {'error': _('Cannot assign a Credential of kind `{}`.').format(kind)}
```

Duplicates the serializer whitelist at the view layer.

**Proposed fix:** Same as serializer fix above — delegate to a
`CredentialType` attribute rather than a hardcoded list. Remove the duplication
between view and serializer.

---

### 8. `CredentialInputSource` — `kind='external'` validation
**File:** `awx/main/models/credential.py:633-639`

```python
def clean_target_credential(self):
    if self.target_credential.credential_type.kind == 'external':
        raise ValidationError(_('Target must be a non-external credential'))

def clean_source_credential(self):
    if self.source_credential.credential_type.kind != 'external':
        raise ValidationError(_('Source must be an external credential'))
```

**Assessment:** This coupling is inherent to the `external` kind concept and
is acceptable. The `external` kind is a structural designator, not a behavioral
one. No change needed here unless the `external`/non-`external` distinction
is itself replaced.

---

## Priority Order

| Priority | Area | Effort | Impact |
|---|---|---|---|
| P1 | Network credential injection bypassing `inject_credential` | Medium | High — directly violates the abstraction contract |
| P1 | Job template credential kind whitelist (serializer + view) | Low | High — blocks future credential kinds |
| P2 | `Credential.needs_*` SSH/vault properties | Medium | Medium — limits new interactive credential types |
| P2 | OpenStack file path special-case | Medium | Medium — requires extending injection API |
| P3 | `JobOptions` kind-based accessors | Low | Low — convenience only, widely used in tests |
| P3 | Inventory source kind-based validation | High | Medium — requires plugin-layer changes |
| P4 | `KIND_CHOICES` enum | Very High | Low short-term — behavioral change only matters if kinds expand |

---

## Files To Change (Summary)

| File | Change |
|---|---|
| `awx/main/models/credential.py` | Move `needs_*` to `CredentialType`; add `assignable_to_job_template` |
| `awx/main/models/jobs.py` | Retain accessors but document them as kind-coupled |
| `awx/main/tasks/jobs.py` | Remove network cred manual injection; remove openstack special-case |
| `awx/main/models/inventory.py` | Replace kind checks with plugin-declared compatibility |
| `awx/api/serializers.py` | Replace kind whitelist with `CredentialType` attribute |
| `awx/api/views/__init__.py` | Same whitelist fix; remove duplication with serializer |
| `awx_plugins` (external repo) | Add network cred injector for `ANSIBLE_NET_*`; add openstack file path injector hook |

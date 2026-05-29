# AWX Projects Integration: Surface Area Analysis

## Overview

The **Projects** feature in AWX represents a SCM-backed or filesystem-based source of Ansible playbooks, roles, and inventory files. A Project syncs content from an external repository and makes it available to Job Templates and Inventory Sources.

---

## Core Models

**File:** `awx/main/models/projects.py`

| Model | Purpose |
|-------|---------|
| `ProjectOptions` | Abstract mixin with all SCM configuration fields |
| `Project` | Main resource — represents a playbook repository |
| `ProjectUpdate` | Execution job for syncing a project from SCM |

### Project Key Fields
- `scm_type` — `''` (manual), `git`, `svn`, `insights`, `archive`
- `scm_url`, `scm_branch`, `scm_refspec`, `scm_clean`, `scm_delete_on_update`, `scm_track_submodules`
- `local_path` — filesystem path relative to `PROJECTS_ROOT`
- `credential` — ForeignKey to SCM or Insights credential
- `default_environment` — ForeignKey to ExecutionEnvironment
- `signature_validation_credential` — content signing validation
- `scm_update_on_launch`, `scm_update_cache_timeout`, `allow_override`
- `scm_revision`, `playbook_files`, `inventory_files` — read-only, populated after sync

### ProjectUpdate Key Fields
- `project` — ForeignKey (CASCADE) to parent Project
- `job_type` — `check` or `run`
- `scm_revision` — revision discovered in this update

---

## API Endpoints

**Files:** `awx/api/urls/project.py`, `awx/api/urls/project_update.py`

### Project
| Endpoint | Methods | Purpose |
|----------|---------|---------|
| `/api/v2/projects/` | GET, POST | List/create |
| `/api/v2/projects/{id}/` | GET, PATCH, PUT, DELETE | CRUD |
| `/api/v2/projects/{id}/playbooks/` | GET | List discovered playbooks |
| `/api/v2/projects/{id}/inventories/` | GET | List discovered inventory files |
| `/api/v2/projects/{id}/scm_inventory_sources/` | GET | Inventory sources using this project |
| `/api/v2/projects/{id}/update/` | GET, POST | Trigger sync |
| `/api/v2/projects/{id}/project_updates/` | GET | History of syncs |
| `/api/v2/projects/{id}/schedules/` | GET, POST | Scheduled syncs |
| `/api/v2/projects/{id}/notification_templates_started/` | GET, POST, DELETE | Notifications |
| `/api/v2/projects/{id}/notification_templates_success/` | GET, POST, DELETE | Notifications |
| `/api/v2/projects/{id}/notification_templates_error/` | GET, POST, DELETE | Notifications |
| `/api/v2/projects/{id}/teams/` | GET | Teams with access |
| `/api/v2/projects/{id}/access_list/` | GET | Users with access |
| `/api/v2/projects/{id}/object_roles/` | GET | RBAC roles |
| `/api/v2/projects/{id}/activity_stream/` | GET | Audit trail |
| `/api/v2/projects/{id}/copy/` | POST | Copy project |

### ProjectUpdate
| Endpoint | Methods | Purpose |
|----------|---------|---------|
| `/api/v2/project_updates/` | GET | List all updates |
| `/api/v2/project_updates/{id}/` | GET, DELETE | Retrieve/delete |
| `/api/v2/project_updates/{id}/cancel/` | POST | Cancel |
| `/api/v2/project_updates/{id}/stdout/` | GET | Console output |
| `/api/v2/project_updates/{id}/events/` | GET | Job events |
| `/api/v2/project_updates/{id}/notifications/` | GET | Notifications sent |
| `/api/v2/project_updates/{id}/scm_inventory_updates/` | GET | Inventory updates spawned |

---

## Serializers

**File:** `awx/api/serializers.py`

| Serializer | Purpose |
|-----------|---------|
| `ProjectOptionsSerializer` | Base with SCM fields |
| `ProjectSerializer` | Full project + status + capabilities |
| `ProjectPlaybooksSerializer` | Returns playbooks array |
| `ProjectInventoriesSerializer` | Returns inventory_files array |
| `ProjectUpdateViewSerializer` | Returns `can_update` |
| `ProjectUpdateSerializer` | Base update fields |
| `ProjectUpdateDetailSerializer` | + playbook/task counts |
| `ProjectUpdateListSerializer` | List view |
| `ProjectUpdateCancelSerializer` | Returns `can_cancel` |

---

## RBAC / Permissions

**File:** `awx/main/models/rbac.py`, `awx/api/permissions.py`

### Project Roles
| Role | Grants | Parent |
|------|--------|--------|
| `admin_role` | Full management | `org.project_admin_role`, `system_administrator` |
| `use_role` | Use in job templates | `admin_role` |
| `update_role` | Trigger updates | `admin_role` |
| `read_role` | View | `org.auditor_role`, `system_auditor`, `use_role`, `update_role` |

### Custom Permissions
- `update_project` — can run a project update
- `use_project` — can use project in a job template

### `ProjectUpdatePermission`
- GET → requires `read` on Project
- POST → requires `start` on Project

---

## SCM Integration

**File:** `awx/main/utils/common.py` (`update_scm_url`)

### Supported SCM Types & URL Schemes
| Type | Schemes |
|------|---------|
| `git` | ssh, git, git+ssh, http, https, ftp, ftps, file |
| `svn` | http, https, svn, svn+ssh, file |
| `insights` | http, https (URL auto-set from `INSIGHTS_URL_BASE`) |
| `archive` | http, https |
| manual | n/a (local filesystem only) |

### Credential Types
- `scm` credential — username, password, ssh_key_data, ssh_key_unlock (git/svn/archive)
- `insights` credential — for Red Hat Insights source

### Special Handling
- GitHub/BitBucket SSH: username forced to `git`, password disallowed
- SCP-style URLs normalized (`git@host:path`)
- IPv6 addresses supported

---

## Project Sync Execution

**File:** `awx/main/tasks/jobs.py` (`RunProjectUpdate`)

### Execution Flow
1. `Project.update()` → creates `ProjectUpdate`, queues via signal
2. `RunProjectUpdate` task picks up and executes:
   - `build_private_data()` — extracts SSH keys from credential
   - `build_passwords()` — SSH unlock, username, password
   - `build_env()` — environment variables (includes Galaxy credentials)
   - `build_args()` — ansible-playbook arguments
   - `build_extra_vars_file()` — variable overrides
   - `build_project_dir()` — prepares local project directory
   - `build_credentials_list()` — gathers all needed credentials
3. Writes discovered `scm_revision`, `playbook_files`, `inventory_files` back to Project

### Lock Management
- `{project_path}.lock` prevents concurrent updates
- Acquired on start, released on finish/cancel

### Cache Management
- `cache_id` determines folder for Galaxy collections/roles cache
- Scoped per project version to avoid collisions

### Auto-Update on Launch
- `scm_update_on_launch` — trigger update before job runs
- `scm_update_cache_timeout` — skip update if synced recently
- `needs_update_on_launch` property evaluated at job start

### Project Directory Cleanup
- **File:** `awx/main/tasks/system.py` (`delete_project_files`)
- Async task removes project directory and lock file on project deletion

---

## Integration: Job Templates & Jobs

**File:** `awx/main/models/jobs.py`

- `JobTemplate.project` — ForeignKey (CASCADE) to Project
- `JobTemplate.scm_branch` — override project branch (requires `allow_override=True`)
- `JobTemplate.ask_scm_branch_on_launch` — prompt for branch at launch
- `Job.project_update` — ForeignKey to the ProjectUpdate that ran before this job
- Project revision passed to jobs via extra vars: `{role}_project_revision`, `{role}_project_scm_branch`

### Validation
- Cannot change project organization if JobTemplates reference it
- Cannot disable `allow_override` if any JobTemplate uses non-default branch or `ask_scm_branch_on_launch`
- Manual projects cannot have: `scm_update_on_launch`, `scm_delete_on_update`, `scm_track_submodules`, `scm_clean`

---

## Integration: Inventory Sources

**File:** `awx/main/models/inventory.py`

- `InventorySource.source_project` — ForeignKey to Project
- `InventorySource.source_path` — path within project directory
- `InventoryUpdate.source_project_update` — ForeignKey to ProjectUpdate that spawned it
- `/api/v2/project_updates/{id}/scm_inventory_updates/` — see inventory updates spawned by a project sync

---

## Integration: Schedules

- `Schedule.unified_job_template` can point to a Project
- `/api/v2/projects/{id}/schedules/` — manage project sync schedules

---

## Integration: Notifications

**File:** `awx/main/models/notifications.py` (`JobNotificationMixin`)

- ProjectUpdate inherits `JobNotificationMixin`
- Sends to `notification_templates_started`, `notification_templates_success`, `notification_templates_error`
- Notification context includes full job fields + summary fields

---

## Integration: Execution Environments

- `Project.default_environment` — ForeignKey to ExecutionEnvironment
- Resolution order for jobs: job EE → job template EE → project EE → org EE → system default
- ProjectUpdate tasks always run in the **control plane EE** (not configurable)

---

## Status Lifecycle

**File:** `awx/main/models/unified_jobs.py`

| Status | Meaning |
|--------|---------|
| `new` / `pending` / `waiting` / `running` | Update in progress |
| `successful` | Last update succeeded |
| `failed` / `error` / `canceled` | Last update failed |
| `never updated` | No update has run |
| `ok` | Manual project — path exists |
| `missing` | Manual project — path not found |

---

## Signals & Lifecycle Hooks

**File:** `awx/main/signals.py`

- Project changes tracked in ActivityStream
- Polymorphic content type registration
- SCM field changes can trigger auto-update on save (unless `skip_update=True`)

---

## Ansible Collection Interface

**Module:** `awx/awx/plugins/modules/project.py`
- create, update, delete projects
- Options: all SCM fields + `wait`, `copy_from`, `check_mode`

**Module:** `awx/awx/plugins/modules/project_update.py`
- Trigger project updates; `wait`, `timeout`

---

## Key Files Summary

| Path | Role |
|------|------|
| `awx/main/models/projects.py` | Project, ProjectUpdate, ProjectOptions models |
| `awx/main/models/jobs.py` | JobTemplate.project integration |
| `awx/main/models/inventory.py` | InventorySource.source_project integration |
| `awx/main/models/unified_jobs.py` | UnifiedJobTemplate base, status choices |
| `awx/main/models/rbac.py` | Project roles |
| `awx/main/models/notifications.py` | Notification mixin |
| `awx/main/models/events.py` | ProjectUpdateEvent |
| `awx/main/models/mixins.py` | TaskManagerProjectUpdateMixin, RelatedJobsMixin |
| `awx/api/urls/project.py` | Project URL routes |
| `awx/api/urls/project_update.py` | ProjectUpdate URL routes |
| `awx/api/views/__init__.py` | All view classes |
| `awx/api/serializers.py` | All serializers |
| `awx/api/permissions.py` | ProjectUpdatePermission |
| `awx/main/tasks/jobs.py` | RunProjectUpdate execution task |
| `awx/main/tasks/system.py` | delete_project_files task |
| `awx/main/utils/common.py` | update_scm_url() validation |
| `awx/main/utils/ansible.py` | Playbook/inventory file discovery helpers |
| `awx/main/signals.py` | ActivityStream, model signals |

---

## Test Coverage

| Type | Path |
|------|------|
| Unit | `awx/main/tests/unit/models/test_project.py` |
| Functional API | `awx/main/tests/functional/api/test_project.py` |
| Functional Model | `awx/main/tests/functional/models/test_project.py` |
| RBAC | `awx/main/tests/functional/rbac/test_rbac_project.py` |
| Live (manual) | `awx/main/tests/live/tests/projects/test_manual_project.py` |
| Live (file) | `awx/main/tests/live/tests/projects/test_file_projects.py` |
| Collection integration | `awx_collection/tests/integration/targets/project/tasks/main.yml` |

---

## Settings Referenced

| Setting | Purpose |
|---------|---------|
| `PROJECTS_ROOT` | Base filesystem directory for project files |
| `INSIGHTS_URL_BASE` | API URL for Insights-type projects |
| `AWX_SHOW_PLAYBOOK_LINKS` | Follow symlinks when listing playbooks |
| `DEFAULT_PROJECT_UPDATE_TIMEOUT` | Global default sync timeout |
| `GALAXY_IGNORE_CERTS` | Skip cert validation for Galaxy |

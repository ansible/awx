# Inventory Integration Surface Area

## Summary

The inventory system is one of the most deeply integrated subsystems in AWX, touching job execution, scheduling, permissions, activity tracking, metrics, and external system integration through a flexible plugin architecture.

**By the numbers:**
- 4 core models, 12+ supporting models
- ~40+ REST API endpoints across 3 URL routing files
- 57 view/viewset classes
- 30 serializer classes
- 61 frontend components
- 3 Ansible collection modules
- 10+ utility/helper files
- 5+ background task functions
- Pluggable architecture for 10+ cloud provider types

---

## 1. Models

**File:** `awx/main/models/inventory.py` (~1443 lines)

### Core Models
| Model | Purpose |
|---|---|
| `Inventory` | Parent container; kind = `''`, `smart`, or `constructed` |
| `Host` | Individual managed hosts |
| `Group` | Named groupings of hosts, hierarchical |
| `InventorySource` | Template for a sync from an external source |
| `InventoryUpdate` | A UnifiedJob representing one sync run |
| `CustomInventoryScript` | User-provided script for custom inventory |

### Supporting Models
| Model | Purpose |
|---|---|
| `InventorySourceOptions` | Shared config fields (mixin for Source and Update) |
| `InventoryConstructedInventoryMembership` | Input inventory membership for constructed |
| `SmartInventoryMembership` | Dynamic host membership for smart inventories |
| `HostMetric` | Per-host performance/usage metrics |
| `HostMetricSummaryMonthly` | Aggregated monthly host metrics |
| `InventoryGroupVariablesWithHistory` | Historical group variable tracking |

### Key Mixins on Inventory Models
- `ResourceMixin` - RBAC and general resource functionality
- `RelatedJobsMixin` - Links to related jobs; blocks deletion if active
- `TaskManagerInventoryUpdateMixin` - Scheduling/task management for updates
- `CustomVirtualEnvMixin` - Custom execution environment support
- `OpaQueryPathMixin` - OPA policy path support

---

## 2. API Endpoints

**URL files:**
- `awx/api/urls/inventory.py`
- `awx/api/urls/inventory_source.py`
- `awx/api/urls/inventory_update.py`

### Inventory (`/api/v2/inventories/`)
| Endpoint | View |
|---|---|
| `GET\|POST /inventories/` | InventoryList |
| `GET\|PUT\|DELETE /inventories/{id}/` | InventoryDetail |
| `GET\|POST /inventories/{id}/hosts/` | InventoryHostsList |
| `GET\|POST /inventories/{id}/groups/` | InventoryGroupsList |
| `GET\|POST /inventories/{id}/root_groups/` | InventoryRootGroupsList |
| `GET /inventories/{id}/variable_data/` | InventoryVariableData |
| `GET /inventories/{id}/script/` | InventoryScriptView |
| `GET /inventories/{id}/tree/` | InventoryTreeView |
| `GET\|POST /inventories/{id}/inventory_sources/` | InventoryInventorySourcesList |
| `GET\|POST /inventories/{id}/input_inventories/` | InventoryInputInventoriesList (constructed) |
| `GET /inventories/{id}/update_inventory_sources/` | InventoryInventorySourcesUpdate |
| `GET /inventories/{id}/activity_stream/` | InventoryActivityStreamList |
| `GET /inventories/{id}/job_templates/` | InventoryJobTemplateList |
| `GET /inventories/{id}/ad_hoc_commands/` | InventoryAdHocCommandsList |
| `GET /inventories/{id}/access_list/` | InventoryAccessList |
| `GET\|POST\|DELETE /inventories/{id}/instance_groups/` | InventoryInstanceGroupsList |
| `GET\|POST\|DELETE /inventories/{id}/labels/` | InventoryLabelList |
| `POST /inventories/{id}/copy/` | InventoryCopy |

### Constructed Inventory
| Endpoint | View |
|---|---|
| `GET\|POST /constructed_inventories/` | ConstructedInventoryList |
| `GET\|PUT\|DELETE /constructed_inventories/{id}/` | ConstructedInventoryDetail |

### Hosts (`/api/v2/hosts/`)
| Endpoint | View |
|---|---|
| `GET\|POST /hosts/` | HostList |
| `GET\|PUT\|DELETE /hosts/{id}/` | HostDetail |
| `GET /hosts/{id}/ansible_facts/` | HostAnsibleFactsDetail |
| `GET\|POST\|DELETE /hosts/{id}/groups/` | HostGroupsList |
| `GET /hosts/{id}/all_groups/` | HostAllGroupsList |
| `GET /hosts/{id}/inventory_sources/` | HostInventorySourcesList |
| `GET /hosts/{id}/smart_inventories/` | HostSmartInventoriesList |
| `GET /hosts/{id}/activity_stream/` | HostActivityStreamList |

### Groups (`/api/v2/groups/`)
| Endpoint | View |
|---|---|
| `GET\|POST /groups/` | GroupList |
| `GET\|PUT\|DELETE /groups/{id}/` | GroupDetail |
| `GET\|POST\|DELETE /groups/{id}/children/` | GroupChildrenList |
| `GET /groups/{id}/potential_children/` | GroupPotentialChildrenList |
| `GET\|POST\|DELETE /groups/{id}/hosts/` | GroupHostsList |
| `GET /groups/{id}/all_hosts/` | GroupAllHostsList |
| `GET /groups/{id}/inventory_sources/` | GroupInventorySourcesList |
| `GET /groups/{id}/activity_stream/` | GroupActivityStreamList |

### Inventory Sources (`/api/v2/inventory_sources/`)
| Endpoint | View |
|---|---|
| `GET\|POST /inventory_sources/` | InventorySourceList |
| `GET\|PUT\|DELETE /inventory_sources/{id}/` | InventorySourceDetail |
| `GET /inventory_sources/{id}/update/` | InventorySourceUpdateView |
| `GET\|POST /inventory_sources/{id}/inventory_updates/` | InventorySourceUpdatesList |
| `GET /inventory_sources/{id}/activity_stream/` | InventorySourceActivityStreamList |
| `GET\|POST /inventory_sources/{id}/schedules/` | InventorySourceSchedulesList |
| `GET\|POST\|DELETE /inventory_sources/{id}/credentials/` | InventorySourceCredentialsList |
| `GET /inventory_sources/{id}/groups/` | InventorySourceGroupsList |
| `GET /inventory_sources/{id}/hosts/` | InventorySourceHostsList |
| `GET\|POST\|DELETE /inventory_sources/{id}/notification_templates_started/` | ... |
| `GET\|POST\|DELETE /inventory_sources/{id}/notification_templates_error/` | ... |
| `GET\|POST\|DELETE /inventory_sources/{id}/notification_templates_success/` | ... |

### Inventory Updates (`/api/v2/inventory_updates/`)
| Endpoint | View |
|---|---|
| `GET /inventory_updates/` | InventoryUpdateList |
| `GET\|DELETE /inventory_updates/{id}/` | InventoryUpdateDetail |
| `POST /inventory_updates/{id}/cancel/` | InventoryUpdateCancel |
| `GET /inventory_updates/{id}/stdout/` | InventoryUpdateStdout |
| `GET /inventory_updates/{id}/notifications/` | InventoryUpdateNotificationsList |
| `GET /inventory_updates/{id}/credentials/` | InventoryUpdateCredentialsList |
| `GET /inventory_updates/{id}/events/` | InventoryUpdateEventsList |

### Host Metrics
| Endpoint | View |
|---|---|
| `GET /host_metrics/` | HostMetricList |
| `DELETE /host_metrics/{id}/` | HostMetricDetail |
| `GET /host_metrics/summary_monthly/` | HostMetricSummaryMonthlyList |

### Bulk Operations
| Endpoint | View |
|---|---|
| `POST /bulk/host_create/` | BulkHostCreateView |
| `POST /bulk/host_delete/` | BulkHostDeleteView |

---

## 3. Serializers

**File:** `awx/api/serializers.py`

- `InventorySerializer` (LabelsListMixin, BaseSerializerWithVariables, OpaQueryPathMixin)
- `ConstructedInventorySerializer`
- `InventoryScriptSerializer`
- `HostSerializer` (BaseSerializerWithVariables)
- `BulkHostSerializer`, `BulkHostCreateSerializer`, `BulkHostDeleteSerializer`
- `HostVariableDataSerializer`
- `GroupSerializer` (BaseSerializerWithVariables)
- `GroupTreeSerializer`, `GroupVariableDataSerializer`
- `InventorySourceOptionsSerializer`
- `InventorySourceSerializer`, `InventorySourceUpdateSerializer`
- `InventorySourceCredentialField`
- `InventoryUpdateSerializer`, `InventoryUpdateDetailSerializer`
- `InventoryUpdateListSerializer`, `InventoryUpdateCancelSerializer`
- `InventoryUpdateEventSerializer`
- `InventoryVariableDataSerializer`
- `JobHostSummarySerializer`

---

## 4. Background Tasks

**File:** `awx/main/tasks/system.py`

| Function | Description |
|---|---|
| `update_inventory_computed_fields(inventory_id)` | Recalculates inventory stats (host count, etc.) |
| `update_smart_memberships_for_inventory(smart_inventory)` | Updates membership for a single smart inventory |
| `update_host_smart_inventory_memberships()` | Periodic sync of all smart inventory memberships |
| `delete_inventory(inventory_id, user_id, retries=5)` | Async deletion with cleanup (timeout: 3600*5s) |

**File:** `awx/main/tasks/jobs.py`

- InventorySource injector loading and credential injection during job execution
- Inventory file generation for job runner
- Smart inventory member caching before job execution
- Environment variable preparation (inventory ID)

**Scheduler:** `awx/main/scheduler/task_manager.py`
- InventoryUpdate dependency management
- Update cache timeout checking
- Scheduled inventory source triggers

---

## 5. Inventory Source Plugin System

**File:** `awx/main/utils/plugins.py`

- `discover_available_cloud_provider_plugin_names()` - Lists loaded cloud plugins
- `compute_cloud_inventory_sources()` - Combines cloud plugins + `scm` + `constructed`
- `load_combined_inventory_source_options()` - Returns all source type metadata
- Entry point groups: `['inventory', 'inventory.supported']`
- Plugins registered in `InventorySourceOptions.injectors` dict

**Supported Source Types:**
- `custom` - Custom script
- `scm` - Source control (project-based)
- `constructed` - Built from other inventories using filters/groups
- `ec2` / `aws` - Amazon Web Services
- `gcp` - Google Cloud Platform
- `azure` - Microsoft Azure
- `vmware` - VMware vCenter
- `vmware_esxi` - VMware ESXi
- `openshift_virtualization` - OpenShift VM inventory
- Additional cloud providers via entry points (AAP-only)

**Each plugin provides:**
- Human-readable description
- Inventory filename used during execution
- Credential validation logic
- Environment/file injectors (`env`, `file`, `extra_env`)

---

## 6. Signals & Hooks

**File:** `awx/main/signals.py`

| Signal | Models | Handler |
|---|---|---|
| `post_save`, `post_delete` | Host | `emit_update_inventory_on_created_or_deleted` |
| `post_save`, `post_delete` | Group | `emit_update_inventory_on_created_or_deleted` |
| `post_save`, `post_delete` | InventorySource | `emit_update_inventory_on_created_or_deleted` |
| `post_save`, `post_delete` | Job | `emit_update_inventory_on_created_or_deleted` |

All signals are deferred via `connection.on_commit()` for transaction safety.

**Context Managers** (`awx/main/utils/common.py`):
- `ignore_inventory_computed_fields()` - Prevents recursive recalculation
- `ignore_inventory_group_removal()` - Handles group deletion edge cases

---

## 7. RBAC & Permissions

**File:** `awx/api/permissions.py`

- Inventory registered with `permission_registry`
- `ImplicitRoleField` for role-based access control
- Roles inherit from organization (org admin can manage org inventories)
- Standard roles: Admin, Use, Update, Ad Hoc, Read

---

## 8. Activity Stream

**File:** `awx/main/models/activity_stream.py`

- `Inventory` - Full change tracking registered
- `InventorySource` - Full change tracking registered
- `InventoryUpdate` - Tracked differently (not direct activity stream)

---

## 9. Special Inventory Types

### Smart Inventories
- `inventory.kind = 'smart'`
- `inventory.host_filter` - QuerySet expression for dynamic membership
- `SmartInventoryMembership` model tracks resolved members
- Synced by `update_host_smart_inventory_memberships()` periodic task
- Cached in `build_smart_inventory_members` before job execution

### Constructed Inventories
- `inventory.kind = 'constructed'`
- Built from input inventories using Jinja2 `compose` and `keyed_groups`
- `InventoryConstructedInventoryMembership` - Tracks input inventory relationships
- `InventoryInputInventoriesList` - Manages input inventories
- `Host.get_source_hosts_for_constructed_inventory()` - Resolves members
- Special serializer (`ConstructedInventorySerializer`) and views

---

## 10. Utilities & Helpers

| File | Purpose |
|---|---|
| `awx/main/utils/inventory_vars.py` | Variable parsing and management |
| `awx/main/utils/mem_inventory.py` | In-memory inventory building during sync |
| `awx/main/utils/handlers.py` | `SpecialInventoryHandler` for sync logging |
| `awx/main/utils/common.py` | Thread-local update flags, context managers |
| `awx/main/utils/plugins.py` | Plugin discovery and loading |

---

## 11. Management Commands

| Command | File | Purpose |
|---|---|---|
| `inventory_import` | `awx/main/management/commands/inventory_import.py` | Bulk import from Ansible inventory files |
| `host_metric` | `awx/main/management/commands/host_metric.py` | Host metric collection and aggregation |
| `cleanup_jobs` | `awx/main/management/commands/cleanup_jobs.py` | Remove old inventory update jobs |
| `create_preload_data` | `awx/main/management/commands/create_preload_data.py` | Seed data including inventories |
| `export_custom_scripts` | `awx/main/management/commands/export_custom_scripts.py` | Export custom inventory scripts |

---

## 12. Frontend Components

**Root:** `awx/ui/src/frontend/awx/`

### Interfaces
- `interfaces/Inventory.ts`
- `interfaces/InventoryGroup.ts`
- `interfaces/InventorySource.ts`

### Routes
- `main/routes/useAwxInventoryRoutes.tsx`

### Page Components (61 files total)
- `inventories/InventoryForm.tsx`
- `inventories/InventoryPage/InventoryDetails.tsx`
- `inventories/InventoryPage/InventoryHosts.tsx`
- `inventories/InventoryPage/InventoryGroups.tsx`
- `inventories/InventoryPage/InventorySources.tsx`
- `inventories/InventoryPage/InventoryJobs.tsx`
- `inventories/InventoryPage/InventoryJobTemplates.tsx`
- `inventories/InventoryPage/InventoryTeamAccess.tsx`
- `inventories/InventoryPage/InventoryUserAccess.tsx`
- `inventories/InventoryRunCommand.tsx`
- `inventories/inventoryGroup/` - Group-specific views
- `inventories/inventoryHostsPage/` - Host-specific views
- `inventories/inventorySources/` - Source management views

### Shared Components
- `components/ConstructedInventoryHint.tsx`
- `components/InventoryAddTeams.tsx`
- `components/InventoryAddUsers.tsx`
- `components/PageFormInventorySelect.tsx`
- `components/PageFormInventorySourceSelect.tsx`
- `hooks/useCancelInventoryUpdate.tsx`
- `hooks/useCopyInventory.tsx`

---

## 13. Ansible Collection

**Directory:** `awx_collection/plugins/modules/`

| Module | Purpose |
|---|---|
| `inventory.py` | Create/update/delete inventories |
| `inventory_source.py` | Create/update/delete inventory sources |
| `inventory_source_update.py` | Trigger inventory update jobs |

**Inventory Plugin:** `awx_collection/plugins/inventory/controller.py`
- Ansible dynamic inventory plugin for pulling inventory from AWX/Controller

---

## 14. Tests

| Path | Coverage Area |
|---|---|
| `awx/main/tests/unit/models/test_inventory.py` | Core model logic |
| `awx/main/tests/unit/api/serializers/test_inventory_serializers.py` | Serializer validation |
| `awx/main/tests/functional/api/test_inventory.py` | API behavior |
| `awx/main/tests/functional/models/test_inventory.py` | Model functional behavior |
| `awx/main/tests/functional/rbac/test_rbac_inventory.py` | Permission/role logic |
| `awx/main/tests/functional/test_inventory_import.py` | Management command |
| `awx/main/tests/functional/test_inventory_source_injectors.py` | Plugin injection |
| `awx/main/tests/functional/test_inventory_input_constructed.py` | Constructed inventory |
| `awx/main/tests/functional/test_inventory_vars.py` | Variable handling |
| `awx/main/tests/functional/test_mem_inventory.py` | In-memory operations |
| `awx/main/tests/functional/test_inventory_source_migration.py` | Migration testing |
| `awx_collection/test/awx/test_inventory.py` | Collection module tests |
| `awx_collection/test/awx/test_inventory_source.py` | Collection source module tests |
| `cypress/e2e/awx/inventories/` | E2E UI tests |
| `cypress/e2e/awx/inventories-source/` | E2E source tests |
| `cypress/e2e/awx/inventory-host/` | E2E host tests |

---

## 15. Integration Points with Other Subsystems

| Subsystem | Integration |
|---|---|
| **Job Templates** | `inventory` FK required (or `ask_inventory_on_launch`); used for host count, slicing, limits |
| **Ad-Hoc Commands** | Run against inventory hosts via `/inventories/{id}/ad_hoc_commands/` |
| **Schedules** | Inventory sources can be scheduled for periodic sync |
| **Credentials** | Cloud credentials attached to InventorySource; SCM credentials for project-based sources |
| **Projects** | Source project for SCM-based inventory sources; branch overrides per source |
| **Notifications** | Start/Success/Error templates per InventorySource |
| **Labels** | Inventory tagging system |
| **Instance Groups** | Inventory sources can specify execution instance group |
| **Analytics** | Host metrics tracking; license consumption monitoring |
| **Execution Environments** | Custom EE per InventorySource via `CustomVirtualEnvMixin` |
| **RBAC/Teams** | Organization-level role inheritance; access list management |
| **Activity Stream** | Full change audit trail for Inventory and InventorySource |

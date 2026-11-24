# External Query Files for Indirect Node Counting

This document describes how to create query files for the Indirect Node Counting feature. Query files define how to extract managed node information from Ansible module execution results.

## Overview

When Ansible modules interact with external systems (VMware, cloud providers, network devices, etc.), they may manage nodes that aren't in the Ansible inventory. Query files tell the Controller how to extract information about these "indirect" managed nodes from module execution data.

## Query File Types

There are two types of query files:

1. **Embedded Query Files**: Shipped within a collection at `extensions/audit/event_query.yml`
2. **External Query Files**: Shipped in the `redhat.indirect_accounting` collection at `extensions/audit/external_queries/<namespace>.<name>.<version>.yml`

Embedded queries take precedence over external queries. External queries support version fallback within the same major version.

## File Format

Query files are YAML documents that map fully-qualified module names to jq expressions.

### Basic Structure

```yaml
---
<namespace>.<collection>.<module_name>:
  query: >-
    <jq_expression>
```

### Example

```yaml
---
community.vmware.vmware_guest:
  query: >-
    {name: .instance.hw_name, canonical_facts: {host_name: .instance.hw_name, uuid: .instance.hw_product_uuid}, facts: {guest_id: .instance.hw_guest_id}}
```

## jq Expression Requirements

The jq expression processes the module's result data (`event_data.res`) and must output a JSON object with the following fields:

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Display name of the indirect managed node |
| `canonical_facts` | object | Facts used for node deduplication across jobs |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `facts` | object | Additional information about the managed node |

### canonical_facts

The `canonical_facts` object should contain fields that uniquely identify the managed node. Common examples:

- `host_name`: The hostname of the managed node
- `uuid`: A unique identifier (VM UUID, device serial number, etc.)
- `ip_address`: IP address if it uniquely identifies the node

These facts are used to deduplicate nodes across multiple job runs. Choose facts that remain stable across the node's lifecycle.

### facts

The `facts` object contains additional metadata that doesn't affect deduplication:

- `device_type`: Type of device (e.g., "virtual_machine", "network_switch")
- `guest_id`: Guest OS identifier
- `platform`: Platform information

## jq Expression Input

The jq expression receives the module's result data as input. This is the `res` field from Ansible's job event data, which typically contains:

- The module's return values
- Any registered variables
- Status information

To understand what data is available, examine the module's documentation or run a test playbook and inspect the job events.

## Module Matching

### Exact Match

Queries are matched by fully-qualified module name:

```yaml
community.vmware.vmware_guest:
  query: >-
    ...
```

This matches only `community.vmware.vmware_guest` module invocations.

### Wildcard Match

You can use wildcards to match all modules in a collection:

```yaml
community.vmware.*:
  query: >-
    ...
```

Exact matches take precedence over wildcard matches.

## External Query File Naming

External query files must follow this naming convention:

```
<namespace>.<collection_name>.<version>.yml
```

Examples:
- `community.vmware.4.5.0.yml`
- `cisco.ios.8.0.0.yml`
- `amazon.aws.7.2.1.yml`

## Version Fallback

When no exact version match exists for an external query, the system falls back to the nearest compatible version:

1. Only versions with the **same major version** are considered
2. The **highest version less than or equal to** the installed version is selected
3. Major version boundaries are never crossed

### Examples

| Installed Version | Available Queries | Query Used | Reason |
|-------------------|-------------------|------------|--------|
| 4.5.0 | 4.0.0, 4.1.0, 5.0.0 | 4.1.0 | Highest v4.x <= 4.5.0 |
| 4.0.5 | 4.0.0, 4.1.0, 5.0.0 | 4.0.0 | 4.1.0 > 4.0.5, so 4.0.0 |
| 5.2.0 | 4.0.0, 4.1.0, 5.0.0 | 5.0.0 | Highest v5.x <= 5.2.0 |
| 3.8.0 | 4.0.0, 4.1.0, 5.0.0 | None | No v3.x queries available |
| 6.0.0 | 4.0.0, 4.1.0, 5.0.0 | None | No v6.x queries available |

## Complete Example

Here's a complete external query file for `community.vmware` version 4.5.0:

**File**: `extensions/audit/external_queries/community.vmware.4.5.0.yml`

```yaml
---
# Query for vmware_guest module - extracts VM information
community.vmware.vmware_guest:
  query: >-
    {name: .instance.hw_name, canonical_facts: {host_name: .instance.hw_name, uuid: .instance.hw_product_uuid}, facts: {guest_id: .instance.hw_guest_id, num_cpus: .instance.hw_processor_count}}

# Query for vmware_guest_info module
community.vmware.vmware_guest_info:
  query: >-
    {name: .instance.hw_name, canonical_facts: {host_name: .instance.hw_name, uuid: .instance.hw_product_uuid}, facts: {power_state: .instance.hw_power_status}}
```

## Testing Query Files

To test a query file:

1. Run a playbook that uses the target module
2. Examine the job events to see the module's result data
3. Test your jq expression against the result data using the `jq` command-line tool
4. Verify the output contains valid `name` and `canonical_facts` fields

Example testing with jq:

```bash
# Sample module result data (from job event)
echo '{"instance": {"hw_name": "test-vm", "hw_product_uuid": "abc-123"}}' | \
  jq '{name: .instance.hw_name, canonical_facts: {host_name: .instance.hw_name, uuid: .instance.hw_product_uuid}}'
```

## Troubleshooting

### Query Not Being Applied

1. Verify the file is in the correct location
2. Check the file naming matches the collection namespace, name, and version exactly
3. Ensure the module name in the query matches the fully-qualified module name

### No Indirect Nodes Counted

1. Verify the jq expression produces valid output with `canonical_facts`
2. Check the Controller logs for jq parsing errors
3. Ensure the module's result data contains the expected fields

### Version Fallback Not Working

1. Verify the fallback version has the same major version as the installed collection
2. Check that the fallback version is less than or equal to the installed version

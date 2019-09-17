# SCM Inventory

Users can create inventory sources that use content in the source tree of
a project as an Ansible inventory source.

## Usage Details

Fields that should be specified on creation of SCM inventory source:

 - `source_project` - project to use
 - `source_path` - relative path inside of the project indicating a
   directory or a file; if left blank, `""` is still a relative path
   indicating the root directory of the project
 - the `source` field should be set to `"scm"`

Additionally:

 - `source_vars` - if these are set on a "file" type inventory source
   then they will be passed to the environment vars when running
 - `update_on_project_update` - if set, a project update of the source
   project will automatically update this inventory source as a side effect

If `update_on_project_update` is not set, then they can manually update
just the inventory source with a POST to its update endpoint,
`/inventory_sources/N/update/`.

If `update_on_project_update` is set, the POST to the inventory source's
update endpoint will trigger an update of the source project, which may,
in turn, trigger an update of the inventory source.
Also, with this flag set, an update _of the project_ is
scheduled immediately after creation of the inventory source.
Also, if this flag is set, no inventory updates will be triggered
_unless the SCM revision of the project changes_.


### RBAC

The user needs the `use` role for the project in order to utilize it as a source
project for the inventory (this entails permission to run arbitrary scripts).
To update the project, they need `update` permission to the project,
even if the update is done indirectly.


### Inventory File Suggestions

The project should show a listing of suggested inventory locations at the `/projects/N/inventories/` endpoint, but this is not a comprehensive list of
all paths that could be used as an Ansible inventory because of the wide
range of inclusion criteria. The list will also max out at 50 entries.
The user should be allowed to specify a location manually in the UI.
This listing should be refreshed to the latest SCM info on a project update.

If no inventory sources use a project as an SCM inventory source, then
the inventory listing may not be refreshed on update.


### Still-to-come 3.2 Changes

As a part of a different feature, it is planned to have all inventory sources
inside of an inventory all update with a single button click. When this
happens for an inventory containing an SCM inventory source, it should
update the project.


### Inventory Source Restriction

Since automatic inventory updates (triggered by a project update) do not
go through the task system, typical protection against conflicting updates
is not available. To avoid problems, only one inventory source is allowed for
inventories that use this feature. That means that if an inventory source
has `source=scm` and `update_on_project_update=true`, it can be the only
inventory source for its inventory.


## Supported File Syntax

> Any Inventory Ansible supports should be supported by this feature.

This is accomplished by making use of the `ansible-inventory` command.
The inventory import `tower-manage` command will check for the existence
of `ansible-inventory` and if it is not present, it will call a backported
version of it. The backport is maintained as its own GPL3 licensed
repository.

https://github.com/ansible/ansible-inventory-backport

Because the internal mechanism is different, there needs to be some coverage
testing with Ansible versions pre-2.4 and after.

### Vars Restrictions

When creating any `scm` type inventory source, the `overwrite_vars` field
must be set to `true`. This should be enforced by API validation and
the UI should also force this setting.

Why? This is because `ansible-inventory` is planned to
return group vars at the group-level in its JSON output, but the backported
script returns them on the host-level. In Ansible 2.4, inventory modules are
being refactored into plugins, and showing vars on the group-level depends on
this. Since it is not possible to _also_ backport the inventory module
refactor to prior Ansible versions, this discrepancy can not be resolved.
While "flattening" the group vars down to the host-level is functionally
equivalent, upgrading Ansible would cause an anomaly in variable precedence.

This future variable precedence problem is avoided by forcing overwriting
of variables until Ansible 2.3 is deprecated, after which all updates
will consistently utilize group-level variables.

# Acceptance Criteria Use Cases

Some test scenarios to look at:
 - Test projects that use scripts
 - Test projects that have multiple inventory files in a directory,
   `group_vars`, `host_vars`, etc.
 - Test scripts in the project repo
 - Test scripts that use environment variables provided by a credential
   in Tower
 - Test multiple inventories that use the same project, pointing to different
   files / directories inside of the project
 - Feature works correctly even if project doesn't have any playbook files
 - File-related errors should surface as inventory import failures
   + missing file
   + invalid syntax in file
 - If the project SCM update encounters errors, it should not run the
   inventory updates

# Notes for Official Documentation

The API guide should summarize what is in the use details.
Once the UI implementation is done, the product docs should cover its
standard use.

## Update-On-Launch

If the SCM inventory source is configured to follow the project updates,
the `update_on_launch` field can not to be set to True. This is because
of concerns related to the task manager job dependency tree.

Below are some alternatives methods which allow a user to accomplish the same thing in a different way:

### Alternative 1: Use same project for playbook

A user can make a job template that uses a project as well as an inventory
that updates from that same project. In this case, they can set the project
to `update_on_launch`, in which case it will trigger an inventory update
if needed.

### Alternative 2: Use the project in a workflow

If a user must utilize a different project for the playbook than for the inventory
source, then they can still place the project in a workflow and then have
a job template run on success of the project update.

This is guaranteed to have the inventory update "on time" (this means
that the inventory changes are complete before the job template is launched),
because the project does not transition to the completed state
until the inventory update is finished.

Note that a failed inventory update does not mark the project as failed.

## Restricting Instance Group to Run Script On

Since SCM inventory sources are running scripts written by people with
access to the source-control, a user may want to restrict which instance
groups the inventory update runs on.

If the inventory source is set to update on project update, it will run
on the same instance (inside of the Tower cluster) as the project update.
This can be restricted by limiting the instance groups of the organization
that contains the `source_project` of the inventory source.

If the inventory source is not configured to update on project update,
then it will inherit the allowed instance groups from its inventory,
like all other inventory syncs.

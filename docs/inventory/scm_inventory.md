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

## Supported File Syntax

> Any Inventory Ansible supports should be supported by this feature.

This is accomplished by making use of the `ansible-inventory` command.

When running an inventory update, the `ansible-inventory` command is invoked,
passing the location specified by `source_path` to the `-i` CLI option.
Then `ansible-inventory` writes JSON data to a file, which is read, parsed,
and then data saved to the database.

# Acceptance Criteria Use Cases

Some test scenarios to look at:
 - Test projects that use scripts
 - Test projects that have multiple inventory files in a directory,
   `group_vars`, `host_vars`, etc.
 - Test scripts in the project repo
 - Test scripts that use environment variables provided by a credential
   in AWX
 - Test multiple inventories that use the same project, pointing to different
   files / directories inside of the project
 - Feature works correctly even if project doesn't have any playbook files
 - File-related errors should surface as inventory import failures
   + missing file
   + invalid syntax in file
 - If the project SCM update encounters errors, it should not run the
   inventory updates

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

Since SCM inventory sources can run scripts written by people with
access to the source-control, a user may want to restrict which instance
groups the inventory update runs on.

If the inventory source is set to update on project update, it will run
on the same instance (inside of the AWX cluster) as the project update.
This can be restricted by limiting the instance groups of the organization
that contains the `source_project` of the inventory source.

If the inventory source is not configured to update on project update,
then it will inherit the allowed instance groups from its inventory,
like all other inventory syncs.

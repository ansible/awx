# SCM Flat File Inventory

Users can create inventory sources that use content in the source tree of
a project as an Ansible inventory file.

## Usage Details

Fields that should be specified on creation of SCM inventory source:

 - `scm_project` - project to use
 - `source_path` - relative path inside of the project indicating a
   directory or a file, if left blank, "" is still a relative path
   indicating the root directory of the project
 - the `source` field should be set to "scm"

Additionally:

 - `source_vars` - if these are set on a "file" type inventory source
   then they will be passed to the environment vars when running

A user should not be able to update this inventory source via through
the endpoint `/inventory_sources/N/update/`. Instead, they should update
the linked project.

An update of the project automatically triggers an inventory update within
the proper context. An update _of the project_ is scheduled immediately
after creation of the inventory source.

The project should show a listing of suggested inventory locations, at the
endpoint `/projects/N/inventories/`, but this is not a comprehensive list of
all paths that could be used as an Ansible inventory because of the wide
range of inclusion criteria. The list will also max out at 50 entries.
The user should be allowed to specify a location manually in the UI.
This listing should be refreshed to latest SCM info on a project update.
If no inventory sources use a project as an SCM inventory source, then
the inventory listing may not be refreshed on update.

### Still-to-come 3.2 Changes

As a part of a different feature, it is planned to have all inventory sources
inside of an inventory all update with a single button click. When this
happens for an inventory containing an SCM inventory source, it should
update the project.

## Supported File Syntax

> Any Inventory Ansible supports should be supported by this feature

This is accomplished by making use of the `ansible-inventory` command.
the inventory import tower-manage command will check for the existnce
of `ansible-inventory` and if it is not present, it will call a backported
version of it. The backport is maintained as its own GPL3 licensed
repository.

https://github.com/ansible/ansible-inventory-backport

Because the internal mechanism is different, we need some coverage
testing with Ansible versions pre-2.4 and after.

# Acceptance Criteria Use Cases

Some test scenarios to look at:
 - Test projects that use scripts
 - Test projects that have multiple inventory files in a directory,
   group_vars, host_vars, etc.
 - Test scripts in the project repo
 - Test scripts that use environment variables provided by a credential
   in Tower
 - Test multiple inventories that use the same project, pointing to different
   files / directories inside of the project
 - Feature works correctly even if project doesn't have any playbook files
 - File related errors should surface as inventory import failures
   + missing file
   + invalid syntax in file
 - If the project SCM update encounters errors, it should not run the
   inventory updates

# Notes for Official Documentation

The API guide should summarize what is in the use details.
Once the UI implementation is done, the product docs should cover its
standard use.

## Update-on-launch

This type of inventory source will not allow the `update_on_launch` field
to be set to True. This is because of concerns related to the task
manager job dependency tree.

We should document the alternatives for a user to accomplish the same thing
through in a different way.

### Alternative 1: Use same project for playbook

You can make a job template that uses a project as well as an inventory
that updates from that same project. In this case, you can set the project
to `update_on_launch`, in which case it will trigger an inventory update
if needed.

### Alternative 2: Use the project in a workflow

If you must use a different project for the playbook than for the inventory
source, then you can still place the project in a workflow and then have
a job template run on success of the project update.

This is guaranteed to have the inventory update "on time" (by this we mean
that the inventory changes are complete before the job template is launched),
because the project does not transition to the completed state
until the inventory update is finished.

Note that a failed inventory update does not mark the project as failed.

## Lazy inventory updates

It should also be noted that not every project update will trigger a
corresponding inventory update. If the project revision has not changed
and the inventory has not been edited, the inventory update will not fire.

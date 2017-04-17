# SCM Flat File Inventory

Users can create inventory sources that use content in the source tree of
a project as an Ansible inventory file.

## Usage Details

Fields that should be specified on creation of SCM inventory source:

 - `scm_project` - project to use
 - `source_path` - relative path inside of the project indicating a
   directory or a file, if left blank, "" is still a relative path
   indicating the root directory of the project

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

This statement is the overall goal and should hold true absolutely for
Ansible version 2.4 and beyond due to the use of `ansible-inventory`.
Versions of Ansible before that may not support all valid inventory syntax
because the internal mechanism is different.

Documentation should reflect the limitations of inventory file syntax
support in old Ansible versions.

# Acceptance Criteria Notes

Some test scenarios to look at:
 - Obviously use a git repo with examples of host patterns, etc.
 - Test multiple inventories that use the same project, pointing to different
   files / directories inside of the project
 - Feature works correctly even if project doesn't have any playbook files
 - File related errors should surface as inventory import failures
   + missing file
   + invalid syntax in file
 - If the project SCM update encounters errors, it should not run the
   inventory updates


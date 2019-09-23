# Transition to Ansible Inventory Plugins

Inventory updates have changed from using scripts, which are vendored as executable Python scripts, to using dynamically-generated YAML files which conform to the specifications of the `auto` inventory plugin.  These are then parsed by their respective inventory plugin.

The major organizational change is that the inventory plugins are part of the Ansible core distribution, whereas the same logic used to be a part of AWX source.


## Prior Background for Transition

AWX used to maintain logic that parsed `.ini` inventory file contents, in addition to interpreting the JSON output of scripts, re-calling with the `--host` option in cases where the `_meta.hostvars` key was not provided.


### Switch to Ansible Inventory

The CLI entry point `ansible-inventory` was introduced in Ansible 2.4. In Tower 3.2, inventory imports began running this command as an intermediary between the inventory and the import's logic to save content to the database. Using `ansible-inventory` eliminates the need to maintain source-specific logic, relying on Ansible's code instead. This also enables consistent data structure output from `ansible-inventory`. There are many valid structures that a script can provide, but the output from `ansible-inventory` will always be the same, thus the AWX logic to parse the content is simplified. This is why even scripts must be ran through the `ansible-inventory` CLI.

Along with this switchover, a backported version of `ansible-inventory` was provided, which supports Ansible versions 2.2 and 2.3.


### Removal of Backport

In AWX 3.0.0 (and Tower 3.5), the backport of `ansible-inventory` was removed, and support for using custom virtual environments was added. This set the minimum version of Ansible necessary to run _any_ inventory update to 2.4.


## Inventory Plugin Versioning

Beginning in Ansible 2.5, inventory sources in Ansible started migrating away from `contrib` scripts (meaning they lived in the `contrib` folder) to the inventory plugin model.

In AWX 4.0.0 (and Tower 3.5) inventory source types start to switch over to plugins, provided that sufficient compatibility is in place for the version of Ansible present in the local virtualenv.

To see in which version the plugin transition will happen, see `awx/main/models/inventory.py` and look for the source name as a subclass of `PluginFileInjector`, and there should be an `initial_version`, which is the first version that was deemed (via testing) to have sufficient parity in the content for its inventory plugin returns. For example, `openstack` will begin using the inventory plugin in Ansible version 2.8. If you run an OpenStack inventory update with Ansible 2.7.x or lower, it will use the script.

The eventual goal is for all source types to have moved to plugins. For any given source, after the `initial_version` for plugin use is higher than the lowest supported Ansible version, the script can be removed and the logic for script credential injection will also be removed.

For example, after AWX no longer supports Ansible 2.7, the script `awx/plugins/openstack_inventory.py` will be removed.


## Changes to Expect in Imports

An effort was made to keep imports working in the exact same way after the switchover. However, the inventory plugins are a fundamental rewrite and many elements of default behavior have changed. These changes also include many backward-incompatible changes. Because of this, what you get via an inventory import will be a superset of what you get from the script but will not match the default behavior you would get from the inventory plugin on the CLI.

Due to the fact that inventory plugins add additional variables, if you downgrade Ansible, you should turn on `overwrite` and `overwrite_vars` to get rid of stale variables (and potentially groups) no longer returned by the import.


### Changes for Compatibility

Programatically-generated examples of inventory file syntax used in updates (with dummy data) can be found in `awx/main/tests/data/inventory/scripts`. These demonstrate the inventory file syntax used to restore old behavior from the inventory scripts.


#### Hostvar Keys and Values

More `hostvars` will appear if the inventory plugins are used. To maintain backward compatibility, the old names are added back where they have the same meaning as a variable returned by the plugin. New names are not removed.

A small number of `hostvars` will be lost because of general deprecation needs.


#### Host Names

In many cases, the host names will change. In all cases, accurate host tracking will still be maintained via the host `instance_id`.


## Writing Your Own Inventory File

If you do not want any of this compatibility-related functionality, then you can add an SCM inventory source that points to your own file. You can also apply a credential of a `managed_by_tower` type to that inventory source that matches the credential you are using, as long as it is not `gce` or `openstack`.

All other sources provide _secrets_ via environment variables.  These can be re-used without any problems for SCM-based inventory, and your inventory file can be used securely to specify non-sensitive configuration details such as the `keyed_groups` (to provide) or `hostvars` (to construct).


## Notes on Technical Implementation of Injectors

For an inventory source with a given value of the `source` field that is of the built-in sources, a credential of the corresponding credential type is required in most cases (ec2 IAM roles are an exception). This privileged credential is obtained by the method `get_cloud_credential`.

The `inputs` for this credential constitute one source of data for running inventory updates. The following fields from the `InventoryUpdate` model are also data sources, including:

 - `source_vars`
 - `source_regions`
 - `instance_filters`
 - `group_by`

The way this data is applied to the environment (including files and environment vars) is highly dependent on the specific source.

With plugins, the inventory file may reference files that contain secrets from the credential. With scripts, typically an environment variable will reference a filename that contains a ConfigParser format file with parameters for the update, and possibly including fields from the credential.


**Caution:** Please do not put secrets from the credential into the inventory file for the plugin. Right now there appears to be no need to do this, and by using environment variables to specify secrets, this keeps open the possibility of showing the inventory file contents to the user as a latter enhancement.

Logic for setup for inventory updates using both plugins and scripts live in the inventory injector class, specific to the source type.

Any credentials which are not source-specific will use the generic injection logic which is also used in playbook runs.
